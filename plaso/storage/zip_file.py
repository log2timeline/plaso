# -*- coding: utf-8 -*-
"""The ZIP-based storage.

The storage mechanism can be described as a collection of storage files
that are stored together in a single ZIP compressed container.

The storage file is essentially split up in two categories:
   +  A store file (further described below).
   +  Other files, these contain grouping information, tag, collection
      information or other metadata describing the content of the store files.

The store itself is a collection of four files:
  plaso_meta.<store_number>
  plaso_proto.<store_number>
  plaso_index.<store_number>
  plaso_timestamps.<store_number>

The plaso_proto file within each store contains several serialized EventObjects
or events that are serialized (as a protobuf). All of the EventObjects within
the plaso_proto file are fully sorted based on time however since the storage
container can contain more than one store the overall storage is not fully
sorted.

The other files that make up the store are:

  + plaso_meta

Simple text file using YAML for storing metadata information about the store.::

  definition, example:
    variable: value
    a_list: [value, value, value]

This can be used to filter out which proto files should be included
in processing.

+ plaso_index

The index file contains an index to all the entries stored within
the protobuf file, so that it can be easily seeked. The layout is:

+-----+-----+-...+
| int | int | ...|
+-----+-----+-...+

Where int is an unsigned integer '<I' that represents the byte offset
into the .proto file where the beginning of the size variable lies.

This can be used to seek the proto file directly to read a particular
entry within the proto file.

  + plaso_timestamps

This is a simple file that contains all the timestamp values of the entries
within the proto file. Each entry is a a long int ('<q') that contains the value
of the EventObject of that timestamps index into the file.

The structure is:
+-----------+-----------+-...-+
| timestamp | timestamp | ... |
+-----------+-----------+-...-+

This is used for time based filtering, where if the 15th entry in this file is
the first entry that is larger than the lower bound, then the index file is used
to seek to the 15th entry inside the proto file.

  + plaso_proto

The structure of a proto file is:
+------+---------------------------------+------+------...+
| size |  protobuf (plaso_storage_proto) | size | proto...|
+------+---------------------------------+------+------...+

For further details about the storage design see:
  http://plaso.kiddaland.net/developer/libraries/storage
"""
# TODO: Go through the storage library to see if it can be split in two, one
# part which will define the storage itself, and can be relatively independent.
# Independent enough to be split into separate project to ease integration by
# other tools. This file will then contain the queueing mechanism and other
# plaso specific mechanism, making it easier to import the storage library.

import collections
import heapq
import logging
# TODO: replace all instances of struct by construct!
import struct
import sys
import zipfile

import construct
from google.protobuf import message
import yaml

from plaso.engine import profiler
from plaso.lib import definitions
from plaso.lib import event
from plaso.lib import limit
from plaso.lib import pfilter
from plaso.lib import timelib
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2
from plaso.serializer import json_serializer
from plaso.serializer import protobuf_serializer


class _EventTagIndexValue(object):
  """Class that defines the event tag index value."""

  TAG_STORE_STRUCT = construct.Struct(
      u'tag_store',
      construct.ULInt32(u'store_number'),
      construct.ULInt32(u'store_index'))

  TAG_UUID_STRUCT = construct.Struct(
      u'tag_uuid',
      construct.PascalString(u'event_uuid'))

  TAG_INDEX_STRUCT = construct.Struct(
      u'tag_index',
      construct.Byte(u'type'),
      construct.ULInt32(u'offset'),
      construct.IfThenElse(
          u'tag',
          lambda ctx: ctx[u'type'] == 1,
          TAG_STORE_STRUCT,
          TAG_UUID_STRUCT))

  TAG_TYPE_UNDEFINED = 0
  TAG_TYPE_NUMERIC = 1
  TAG_TYPE_UUID = 2

  def __init__(self, identifier, store_number=0, store_offset=0):
    """Initializes the tag index value.

    Args:
      identifier: the identifier string.
      store_number: optional store number.
      store_offset: optional offset relative to the start of the store.
    """
    super(_EventTagIndexValue, self).__init__()
    self.identifier = identifier
    self.store_number = store_number
    self.store_offset = store_offset

  @classmethod
  def Read(cls, file_object, store_number):
    """Reads a tag index value from the file-like object.

    Args:
      file_object: the file-like object to read from.
      store_number: the store number.

    Returns:
      The tag index value if successful or None.
    """
    try:
      tag_index_struct = cls.TAG_INDEX_STRUCT.parse_stream(file_object)
    except (construct.FieldError, AttributeError):
      return None

    tag_type = tag_index_struct.get(u'type', cls.TAG_TYPE_UNDEFINED)
    if tag_type not in [cls.TAG_TYPE_NUMERIC, cls.TAG_TYPE_UUID]:
      logging.warning(u'Unsupported tag type: {0:d}'.format(tag_type))
      return None

    tag_entry = tag_index_struct.get('tag', {})
    if tag_type == cls.TAG_TYPE_NUMERIC:
      tag_identifier = u'{0:d}:{1:d}'.format(
          tag_entry.get(u'store_number', 0),
          tag_entry.get(u'store_index', 0))

    else:
      tag_identifier = tag_entry.get(u'event_uuid', '0')

    store_offset = tag_index_struct.get(u'offset')
    return _EventTagIndexValue(
        tag_identifier, store_number=store_number, store_offset=store_offset)


class _SerializedDataStream(object):
  """Class that defines a serialized data stream."""

  _DATA_ENTRY = construct.Struct(
      u'data_entry',
      construct.ULInt32(u'size'))
  _DATA_ENTRY_SIZE = _DATA_ENTRY.sizeof()

  # The maximum serialized data size (40 MiB).
  _MAXIMUM_DATA_SIZE = 40 * 1024 * 1024

  def __init__(self, zip_file, stream_name, access_mode='r'):
    """Initializes a serialized data stream object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      stream_name: string containing the name of the stream.
      access_mode: optional string containing the access mode.
                   The default is read-only ('r').
    """
    super(_SerializedDataStream, self).__init__()
    self._access_mode = access_mode
    self._entry_index = 0
    self._file_object = None
    self._stream_name = stream_name
    self._stream_offset = 0
    self._zip_file = zip_file

  @property
  def entry_index(self):
    """The entry index."""
    return self._entry_index

  def _OpenFileObject(self):
    """Opens the file-like object (instance of ZipExtFile).

    Raises:
      IOError: if the file-like object cannot be opened.
    """
    try:
      self._file_object = self._zip_file.open(
          self._stream_name, mode=self._access_mode)
    except KeyError as exception:
      raise IOError(
          u'Unable to open stream with error: {0:s}'.format(exception))

    self._stream_offset = 0

  def _ReOpenFileObject(self):
    """Reopens the file-like object (instance of ZipExtFile)."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

    self._file_object = self._zip_file.open(
        self._stream_name, mode=self._access_mode)
    self._stream_offset = 0

  def ReadEntry(self):
    """Reads an entry from the data stream.

    Returns:
      A binary string containing the data or None if there is no data
      remaining.

    Raises:
      IOError: if the entry cannot be read.
    """
    if not self._file_object:
      self._OpenFileObject()

    data = self._file_object.read(self._DATA_ENTRY_SIZE)
    if not data:
      return

    try:
      data_entry = self._DATA_ENTRY.parse(data)
    except construct.FieldError as exception:
      raise IOError(
          u'Unable to read data entry with error: {0:s}'.format(exception))

    if data_entry.size > self._MAXIMUM_DATA_SIZE:
      raise IOError(
          u'Unable to read data entry size value out of bounds.')

    data = self._file_object.read(data_entry.size)
    if len(data) != data_entry.size:
      raise IOError(u'Unable to read data.')

    self._stream_offset += self._DATA_ENTRY_SIZE + data_entry.size
    self._entry_index += 1

    return data

  def SeekEntryAtOffset(self, entry_index, stream_offset):
    """Seeks a specific serialized data stream entry at a specific offset.

    Args:
      entry_index: an integer containing the serialized data stream entry index.
      stream_offset: an integer containing the data stream offset.
    """
    if not self._file_object:
      self._OpenFileObject()

    if stream_offset < self._stream_offset:
      # Since zipfile.ZipExtFile is not seekable we need to close the stream
      # and reopen it to fake a seek.
      self._ReOpenFileObject()

      skip_read_size = stream_offset
    else:
      skip_read_size = stream_offset - self._stream_offset

    if skip_read_size > 0:
      # Since zipfile.ZipExtFile is not seekable we need to read upto
      # the stream offset.
      self._file_object.read(skip_read_size)
      self._stream_offset += skip_read_size

    self._entry_index = entry_index


class _SerializedDataOffsetTable(object):
  """Class that defines a serialized data offset table."""

  _TABLE_ENTRY = construct.Struct(
      u'table_entry',
      construct.ULInt32(u'offset'))
  _TABLE_ENTRY_SIZE = _TABLE_ENTRY.sizeof()

  def __init__(self, zip_file, stream_name, access_mode='r'):
    """Initializes a serialized data offset table object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      stream_name: string containing the name of the stream.
      access_mode: optional string containing the access mode.
                   The default is read-only ('r').
    """
    super(_SerializedDataOffsetTable, self).__init__()
    self._access_mode = access_mode
    self._offsets = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  def GetOffset(self, entry_index):
    """Retrieves a specific serialized data offset.

    Args:
      entry_index: an integer containing the table entry index.

    Returns:
      An integer containing the serialized data offset.

    Raises:
      IndexError: if the table entry index is out of bounds.
    """
    return self._offsets[entry_index]

  def Read(self):
    """Reads the serialized data offset table.

    Raises:
      IOError: if the offset table cannot be read.
    """
    try:
      file_object = self._zip_file.open(
          self._stream_name, mode=self._access_mode)
    except KeyError as exception:
      raise IOError(
          u'Unable to open stream with error: {0:s}'.format(exception))

    try:
      entry_data = file_object.read(self._TABLE_ENTRY_SIZE)
      while entry_data:
        table_entry = self._TABLE_ENTRY.parse(entry_data)

        self._offsets.append(table_entry.offset)
        entry_data = file_object.read(self._TABLE_ENTRY_SIZE)

    except construct.FieldError as exception:
      raise IOError(
          u'Unable to read table entry with error: {0:s}'.format(exception))

    finally:
      file_object.close()


class _SerializedDataTimestampTable(object):
  """Class that defines a serialized data timestamp table."""

  _TABLE_ENTRY = construct.Struct(
      u'table_entry',
      construct.SLInt64(u'timestamp'))
  _TABLE_ENTRY_SIZE = _TABLE_ENTRY.sizeof()

  def __init__(self, zip_file, stream_name, access_mode='r'):
    """Initializes a serialized data timestamp table object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      stream_name: string containing the name of the stream.
      access_mode: optional string containing the access mode.
                   The default is read-only ('r').
    """
    super(_SerializedDataTimestampTable, self).__init__()
    self._access_mode = access_mode
    self._timestamps = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  @property
  def number_of_timestamps(self):
    """The number of timestamps."""
    return len(self._timestamps)

  def GetTimestamp(self, entry_index):
    """Retrieves a specific serialized data timestamp.

    Args:
      entry_index: an integer containing the table entry index.

    Returns:
      An integer containing the serialized data timestamp.

    Raises:
      IndexError: if the table entry index is out of bounds.
    """
    return self._timestamps[entry_index]

  def Read(self):
    """Reads the serialized data timestamp table.

    Raises:
      IOError: if the timestamp table cannot be read.
    """
    try:
      file_object = self._zip_file.open(
          self._stream_name, mode=self._access_mode)
    except KeyError as exception:
      raise IOError(
          u'Unable to open stream with error: {0:s}'.format(exception))

    try:
      entry_data = file_object.read(self._TABLE_ENTRY_SIZE)
      while entry_data:
        table_entry = self._TABLE_ENTRY.parse(entry_data)

        self._timestamps.append(table_entry.timestamp)
        entry_data = file_object.read(self._TABLE_ENTRY_SIZE)

    except construct.FieldError as exception:
      raise IOError(
          u'Unable to read table entry with error: {0:s}'.format(exception))

    finally:
      file_object.close()


class ZIPStorageFile(object):
  """Class that defines the ZIP-based storage file.

  This class contains the lower-level stream management functionality.

  The ZIP-based storagefile contains several streams (files) that contain
  serialized event objects named:

        plaso_proto.###

  Where ### is an increasing integer that starts at 1.
  """

  # The maximum number of cached tables.
  _MAXIMUM_NUMBER_OF_CACHED_TABLES = 5

  def __init__(self):
    """Initializes a ZIP-based storage file object."""
    super(ZIPStorageFile, self).__init__()
    self._event_object_streams = {}
    self._offset_tables = {}
    self._offset_tables_lfu = []
    self._timestamp_tables = {}
    self._timestamp_tables_lfu = []
    self._zipfile = None

  def _GetSerializedEventObjectOffsetTable(self, stream_number):
    """Retrieves the serialized event object stream offset table.

    Args:
      stream_number: an integer containing the number of the stream.

    Returns:
      A serialized data offset table (instance of _SerializedDataOffsetTable).

    Raises:
      IOError: if the stream cannot be opened.
    """
    offset_table = self._offset_tables.get(stream_number, None)
    if not offset_table:
      stream_name = u'plaso_index.{0:06d}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)
      offset_table.Read()

      if len(self._offset_tables) >= self._MAXIMUM_NUMBER_OF_CACHED_TABLES:
        lfu_stream_number = self._offset_tables_lfu.pop()
        del self._offset_tables[lfu_stream_number]

      self._offset_tables[stream_number] = offset_table

    if stream_number in self._offset_tables_lfu:
      lfu_index = self._offset_tables_lfu.index(stream_number)
      self._offset_tables_lfu.pop(lfu_index)

    self._offset_tables_lfu.append(stream_number)

    return offset_table

  def _GetSerializedEventObjectStream(self, stream_number):
    """Retrieves the serialized event object stream.

    Args:
      stream_number: an integer containing the number of the stream.

    Returns:
      A serialized data stream object (instance of _SerializedDataStream).

    Raises:
      IOError: if the stream cannot be opened.
    """
    data_stream = self._event_object_streams.get(stream_number, None)
    if not data_stream:
      stream_name = u'plaso_proto.{0:06d}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(self._zipfile, stream_name)
      self._event_object_streams[stream_number] = data_stream

    return data_stream

  def _GetSerializedEventObjectStreamNumbers(self):
    """Retrieves the available serialized event object stream numbers.

    Returns:
      A sorted list of integers of the available serialized data stream numbers.
    """
    stream_numbers = []
    for stream_name in self._zipfile.namelist():
      if not stream_name.startswith(u'plaso_proto'):
        continue

      _, _, stream_number = stream_name.partition(u'.')
      try:
        stream_number = int(stream_number, 10)
        stream_numbers.append(stream_number)
      except ValueError:
        logging.error(
            u'Unable to determine stream number from stream: {0:s}'.format(
                stream_name))

    return sorted(stream_numbers)

  def _GetStreamNames(self):
    """Retrieves the stream names.

    Yields:
      A string containing the stream name.
    """
    if self._zipfile:
      for stream_name in self._zipfile.namelist():
        yield stream_name

  def _HasStream(self, stream_name):
    """Determines if the ZIP file contains a specific stream.

    Args:
      stream_name: string containing the name of the stream.

    Returns:
      A boolean indicating if the ZIP file contains the stream.
    """
    try:
      file_object = self._zipfile.open(stream_name, 'r')
    except KeyError:
      return False

    file_object.close()
    return True

  def _WriteStream(self, stream_name, stream_data):
    """Write the data to a stream.

    Args:
      stream_name: string containing the name of the stream.
      stream_data: the data of the steam.
    """
    # TODO: this can raise an IOError e.g. "Stale NFS file handle".
    # Determine if this be handled more error resiliently.
    self._zipfile.writestr(stream_name, stream_data)


class StorageFile(ZIPStorageFile):
  """Class that defines the ZIP-based storage file."""

  _STREAM_DATA_SEGMENT_SIZE = 1024

  # Set the maximum buffer size to 196 MiB
  MAXIMUM_BUFFER_SIZE = 196 * 1024 * 1024

  # Set the maximum protobuf string size to 40 MiB
  MAXIMUM_PROTO_STRING_SIZE = 40 * 1024 * 1024

  # Set the maximum report protobuf string size to 24 MiB
  MAXIMUM_REPORT_PROTOBUF_SIZE = 24 * 1024 * 1024

  # Set the version of this storage mechanism.
  STORAGE_VERSION = 1

  source_short_map = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      u'SourceShort'].values:
    source_short_map[value.name] = value.number

  def __init__(
      self, output_file, buffer_size=0, read_only=False, pre_obj=None,
      serializer_format=definitions.SERIALIZER_FORMAT_PROTOBUF):
    """Initializes the storage file.

    Args:
      output_file: The name of the output file.
      buffer_size: Optional maximum size of a single storage (protobuf) file.
                   The default is 0, which indicates no limit.
      read_only: Optional boolean to indicate we are opening the storage file
                 for reading only. The default is false.
      pre_obj: Optional preprocessing object that gets stored inside
               the storage file. The default is None.
      serializer_format: Optional storage serializer format. The default is
                         protobuf.

    Raises:
      IOError: if we open up the file in read only mode and the file does
      not exist.
    """
    super(StorageFile, self).__init__()
    # bound_first and bound_last contain timestamps and None is used
    # to indicate not set.
    self._bound_first = None
    self._bound_last = None
    self._buffer = []
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0
    self._buffer_size = 0
    self._event_object_serializer = None
    self._event_tag_index = None
    self._file_open = False
    self._file_number = 1
    self._first_file_number = None
    self._max_buffer_size = buffer_size or self.MAXIMUM_BUFFER_SIZE
    self._merge_buffer = None
    self._output_file = output_file
    self._pre_obj = pre_obj
    self._read_only = read_only
    self._serializer_format_string = u''
    self._write_counter = 0

    self._SetSerializerFormat(serializer_format)

    self._Open()

    # Add information about the serializer used in the storage.
    if not self._read_only and not self._OpenStream(u'serializer.txt'):
      self._WriteStream(u'serializer.txt', self._serializer_format_string)

    # Attributes for profiling.
    self._enable_profiling = False
    self._profiling_sample = 0
    self._serializers_profiler = None

    self.store_range = None

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  @property
  def file_path(self):
    """The file path."""
    return self._output_file

  @property
  def serialization_format(self):
    """The serialization format."""
    return self._serializer_format_string

  def _BuildTagIndex(self):
    """Builds the tag index that contains the offsets for each tag.

    Raises:
      IOError: if the stream cannot be opened.
    """
    self._event_tag_index = {}

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(u'plaso_tag_index.'):
        continue

      file_object = self._OpenStream(stream_name, u'r')
      if file_object is None:
        raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

      _, _, store_number = stream_name.rpartition(u'.')
      try:
        store_number = int(store_number, 10)
      except ValueError as exception:
        raise IOError((
            u'Unable to determine store number of stream: {0:s} '
            u'with error: {1:s}').format(stream_name, exception))

      while True:
        tag_index_value = _EventTagIndexValue.Read(
            file_object, store_number)
        if tag_index_value is None:
          break

        self._event_tag_index[tag_index_value.identifier] = tag_index_value

  def _FlushBuffer(self):
    """Flushes the buffered streams to disk."""
    if not self._buffer_size:
      return

    yaml_dict = {
        u'range': (self._buffer_first_timestamp, self._buffer_last_timestamp),
        u'version': self.STORAGE_VERSION,
        u'data_type': list(self._count_data_type.viewkeys()),
        u'parsers': list(self._count_parser.viewkeys()),
        u'count': len(self._buffer),
        u'type_count': self._count_data_type.most_common()}
    self._count_data_type = collections.Counter()
    self._count_parser = collections.Counter()

    stream_name = u'plaso_meta.{0:06d}'.format(self._file_number)
    # TODO: why have YAML serialization here?
    self._WriteStream(stream_name, yaml.safe_dump(yaml_dict))

    ofs = 0
    proto_str = []
    index_str = []
    timestamp_str = []
    for _ in range(len(self._buffer)):
      timestamp, entry = heapq.heappop(self._buffer)
      # TODO: Instead of appending to an array
      # which is not optimal (loads up the entire max file
      # size into memory) Zipfile should be extended to
      # allow appending to files (implement lock).
      try:
        # Appending a timestamp to the timestamp index, this is used during
        # time based filtering. If this is not done we would need to unserialize
        # all events to get the timestamp value which is really slow.
        timestamp_str.append(struct.pack('<q', timestamp))
      except struct.error as exception:
        # TODO: Instead of just logging the error unserialize the event
        # and print out information from the event, eg. parser and path spec
        # location. That way we can find the root cause and fix that instead of
        # just catching the exception.
        logging.error((
            u'Unable to store event, not able to index timestamp value with '
            u'error: {0:s} [timestamp: {1:d}]').format(exception, timestamp))
        continue
      index_str.append(struct.pack('<I', ofs))
      packed = struct.pack('<I', len(entry)) + entry
      ofs += len(packed)
      proto_str.append(packed)

    stream_name = u'plaso_index.{0:06d}'.format(self._file_number)
    self._WriteStream(stream_name, b''.join(index_str))

    stream_name = u'plaso_proto.{0:06d}'.format(self._file_number)
    self._WriteStream(stream_name, b''.join(proto_str))

    stream_name = u'plaso_timestamps.{0:06d}'.format(self._file_number)
    self._WriteStream(stream_name, b''.join(timestamp_str))

    self._file_number += 1
    self._buffer_size = 0
    self._buffer = []
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0

  def _GetEventObject(self, stream_number, entry_index=-1):
    """Reads an event object from a specific stream.

    Args:
      stream_number: an integer containing the number of the serialized event
                     object stream.
      entry_index: an integer containing the number of the serialized event
                   object within the stream. Where -1 represents the next
                   available event object.

    Returns:
      An event object (instance of EventObject) or None.
    """
    event_object_data, entry_index = self._GetEventObjectSerializedData(
        stream_number, entry_index=entry_index)
    if not event_object_data:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'event_object')

    event_object = self._event_object_serializer.ReadSerialized(
        event_object_data)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'event_object')

    event_object.store_number = stream_number
    event_object.store_index = entry_index

    return event_object

  def _GetEventObjectSerializedData(self, stream_number, entry_index=-1):
    """Retrieves specific event object serialized data.

    By default the first available entry in the specific serialized stream
    is read, however any entry can be read using the index stream.

    Args:
      stream_number: an integer containing the number of the stream.
      entry_index: Read a specific entry in the file. The default is -1,
                   which represents the first available entry.

    Returns:
      A tuple containing the event object serialized data and the entry index
      of the event object within the storage file.

    Raises:
      IOError: if the stream cannot be opened.
    """
    try:
      data_stream = self._GetSerializedEventObjectStream(stream_number)
    except IOError as exception:
      logging.error((
          u'Unable to retrieve serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    if (not data_stream.entry_index and entry_index == -1 and
        self._bound_first is not None):
      # We only get here if the following conditions are met:
      #   1. data_stream.entry_index is not set (so this is the first read
      #      from this file).
      #   2. There is a lower bound (so we have a date filter).
      #   3. We are accessing this function using 'get me the next entry' as an
      #      opposed to the 'get me entry X', where we just want to server entry
      #      X.
      #
      # The purpose: speed seeking into the storage file based on time. Instead
      # of spending precious time reading through the storage file and
      # deserializing protobufs just to compare timestamps we read a much
      # 'cheaper' file, one that only contains timestamps to find the proper
      # entry into the storage file. That way we'll get to the right place in
      # the file and can start reading protobufs from the right location.

      stream_name = u'plaso_timestamps.{0:06d}'.format(stream_number)
      if self._HasStream(stream_name):
        try:
          entry_index = self._GetFirstSerializedDataStreamEntryIndex(
              stream_number, self._bound_first)

        except IOError as exception:
          entry_index = None

          logging.error(
              u'Unable to read timestamp table from stream: {0:s}.'.format(
                  stream_name))

        if entry_index is None:
          return None, None

      # TODO: determine if anything else needs to be handled here.

    if entry_index >= 0:
      try:
        offset_table = self._GetSerializedEventObjectOffsetTable(stream_number)
        stream_offset = offset_table.GetOffset(entry_index)
      except (IOError, IndexError):
        logging.error((
            u'Unable to read entry index: {0:d} from serialized data stream: '
            u'{1:d}').format(entry_index, stream_number))
        return None, None

      data_stream.SeekEntryAtOffset(entry_index, stream_offset)

    event_object_entry_index = data_stream.entry_index
    try:
      event_object_data = data_stream.ReadEntry()
    except IOError as exception:
      logging.error((
          u'Unable to read entry from serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    return event_object_data, event_object_entry_index

  def _GetEventTagIndexValue(self, store_number, entry_index, uuid):
    """Retrieves an event tag index value.

    Args:
      store_number: the store number.
      entry_index: an integer containing the serialized data stream entry index.
      uuid: the UUID string.

    Returns:
      An event tag index value (instance of _EventTagIndexValue).
    """
    if self._event_tag_index is None:
      self._BuildTagIndex()

    # Try looking up event tag by numeric identifier.
    tag_identifier = u'{0:d}:{1:d}'.format(store_number, entry_index)
    tag_index_value = self._event_tag_index.get(tag_identifier, None)

    # Try looking up event tag by UUID.
    if tag_index_value is None:
      tag_index_value = self._event_tag_index.get(uuid, None)

    return tag_index_value

  def _GetFirstSerializedDataStreamEntryIndex(self, stream_number, timestamp):
    """Retrieves the first serialized data stream entry index for a timestamp.

    The timestamp indicates the lower bound. The first entry with a timestamp
    greater or equal to the lower bound will be returned.

    Args:
      stream_number: an integer containing the number of the stream.
      timestamp: the lower bounds timestamp which is an integer containing
                 the number of micro seconds since January 1, 1970,
                 00:00:00 UTC.

    Returns:
      The index of the entry in the corresponding serialized data stream or
      None if there was no matching entry.

    Raises:
      IOError: if the stream cannot be opened.
    """
    timestamp_table = self._timestamp_tables.get(stream_number, None)
    if not timestamp_table:
      stream_name = u'plaso_timestamps.{0:06d}'.format(stream_number)
      timestamp_table = _SerializedDataTimestampTable(
          self._zipfile, stream_name)
      timestamp_table.Read()

      if len(self._timestamp_tables) >= self._MAXIMUM_NUMBER_OF_CACHED_TABLES:
        lfu_stream_number = self._timestamp_tables_lfu.pop()
        del self._timestamp_tables[lfu_stream_number]

      self._timestamp_tables[stream_number] = timestamp_table

    if stream_number in self._timestamp_tables_lfu:
      lfu_index = self._timestamp_tables_lfu.index(stream_number)
      self._timestamp_tables_lfu.pop(lfu_index)

    self._timestamp_tables_lfu.append(stream_number)

    for entry_index in range(timestamp_table.number_of_timestamps):
      timestamp_compare = timestamp_table.GetTimestamp(entry_index)
      if timestamp_compare >= timestamp:
        return entry_index

  def _InitializeMergeBuffer(self):
    """Initializes the merge buffer."""
    if self.store_range is None:
      number_range = self._GetSerializedEventObjectStreamNumbers()
    else:
      number_range = self.store_range

    self._merge_buffer = []
    for store_number in number_range:
      event_object = self._GetEventObject(store_number)
      if not event_object:
        return

      while event_object.timestamp < self._bound_first:
        event_object = self._GetEventObject(store_number)
        if not event_object:
          return

      heapq.heappush(
          self._merge_buffer,
          (event_object.timestamp, store_number, event_object))

  def _Open(self):
    """Opens the storage file.

    Raises:
      IOError: if the file is opened in read only mode and the file does
               not exist.
    """
    if self._read_only:
      access_mode = u'r'
    else:
      access_mode = u'a'

    try:
      self._zipfile = zipfile.ZipFile(
          self._output_file, access_mode, zipfile.ZIP_DEFLATED, allowZip64=True)
    except zipfile.BadZipfile as exception:
      raise IOError(u'Unable to read ZIP file with error: {0:s}'.format(
          exception))

    self._file_open = True

    # Read the serializer string (if available).
    serializer = self._ReadStream(u'serializer.txt')
    if serializer:
      self._SetSerializerFormat(serializer)

    if not self._read_only:
      logging.debug(u'Writing to ZIP file with buffer size: {0:d}'.format(
          self._max_buffer_size))

      if self._pre_obj:
        self._pre_obj.counter = collections.Counter()
        self._pre_obj.plugin_counter = collections.Counter()

      # Start up a counter for modules in buffer.
      self._count_data_type = collections.Counter()
      self._count_parser = collections.Counter()

      # Need to get the last number in the list.
      for stream_name in self._GetStreamNames():
        if stream_name.startswith(u'plaso_meta.'):
          _, _, file_number = stream_name.partition(u'.')

          try:
            file_number = int(file_number, 10)
            if file_number >= self._file_number:
              self._file_number = file_number + 1
          except ValueError:
            # Ignore invalid metadata stream names.
            pass

      self._first_file_number = self._file_number

  def _OpenStream(self, stream_name, mode='r'):
    """Opens a stream.

    Args:
      stream_name: string containing the name of the stream.
      mode: optional string containing the access mode. The default is
            read-only ('r').

    Returns:
      The stream file-like object (instance of zipfile.ZipExtFile) or None.
    """
    try:
      return self._zipfile.open(stream_name, mode)
    except KeyError:
      return

  def _ProfilingStop(self):
    """Stops the profiling."""
    if self._serializers_profiler:
      self._serializers_profiler.Write()

  def _ReadEventGroup(self, data_stream):
    """Reads an event group.

    Args:
      data_stream: the data stream object (instance of _SerializedDataStream).

    Returns:
      An event group object (instance of plaso_storage_pb2.EventGroup) or None.
    """
    event_group_data = data_stream.ReadEntry()
    if not event_group_data:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'event_group')

    # TODO: add event group serializers and use ReadSerialized.
    # event_group = self._event_group_serializer.ReadSerialized(proto_string)

    event_group = plaso_storage_pb2.EventGroup()
    event_group.ParseFromString(event_group_data)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'event_group')

    # TODO: return a Python object instead of a protobuf.
    return event_group

  def _ReadEventTag(self, data_stream):
    """Reads an event tag.

    Args:
      data_stream: the data stream object (instance of _SerializedDataStream).

    Returns:
      An event tag object (instance of EventTag) or None.
    """
    event_tag_data = data_stream.ReadEntry()
    if not event_tag_data:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'event_tag')

    event_tag = self._event_tag_serializer.ReadSerialized(event_tag_data)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'event_tag')

    return event_tag

  def _ReadEventTagByIdentifier(self, store_number, entry_index, uuid):
    """Reads an event tag by identifier.

    Args:
      store_number: the store number.
      entry_index: an integer containing the serialized data stream entry index.
      uuid: the UUID string.

    Returns:
      The event tag (instance of EventTag).

    Raises:
      IOError: if the event tag data stream cannot be opened.
    """
    tag_index_value = self._GetEventTagIndexValue(
        store_number, entry_index, uuid)
    if tag_index_value is None:
      return

    stream_name = u'plaso_tagging.{0:06d}'.format(tag_index_value.store_number)
    if not self._HasStream(stream_name):
      raise IOError(u'No such stream: {0:s}'.format(stream_name))

    data_stream = _SerializedDataStream(self._zipfile, stream_name)
    data_stream.SeekEntryAtOffset(entry_index, tag_index_value.store_offset)
    return data_stream.ReadEntry()

  def _ReadMeta(self, number):
    """Return a dict with the metadata entries.

    Args:
      number: The number of the metadata file (name is plaso_meta_XXX where
              XXX is this number.

    Returns:
      A dict object containing all the variables inside the metadata file.

    Raises:
      IOError: if the stream cannot be opened.
    """
    stream_name = u'plaso_meta.{0:06d}'.format(number)
    file_object = self._OpenStream(stream_name, 'r')
    if file_object is None:
      raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))
    return yaml.safe_load(file_object)

  def _ReadPreprocessObject(self, data_stream):
    """Reads a preprocessing object.

    Args:
      data_stream: the data stream object (instance of _SerializedDataStream).

    Returns:
      An preprocessing object (instance of PreprocessObject) or None.
    """
    preprocess_data = data_stream.ReadEntry()
    if not preprocess_data:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'pre_obj')

    try:
      preprocess_object = self._pre_obj_serializer.ReadSerialized(
          preprocess_data)
    except message.DecodeError as exception:
      logging.error((
          u'Unable to read serialized preprocessing object '
          u'with error: {0:s}').format(exception))
      return

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'pre_obj')

    return preprocess_object

  def _ReadStream(self, stream_name):
    """Reads the data in a stream.

    Args:
      stream_name: string containing the name of the stream.

    Returns:
      A byte string containing the data of the stream.
    """
    data_segments = []
    file_object = self._OpenStream(stream_name, u'r')

    # zipfile.ZipExtFile does not support the with-statement interface.
    if file_object:
      data = file_object.read(self._STREAM_DATA_SEGMENT_SIZE)
      while data:
        data_segments.append(data)
        data = file_object.read(self._STREAM_DATA_SEGMENT_SIZE)

      file_object.close()

    return b''.join(data_segments)

  def _SetSerializerFormat(self, serializer_format):
    """Set the serializer format.

    Args:
      serializer_format: The storage serializer format.

    Raises:
      ValueError: if the serializer format is not supported.
    """
    if serializer_format == definitions.SERIALIZER_FORMAT_JSON:
      self._serializer_format_string = u'json'

      self._analysis_report_serializer = (
          json_serializer.JSONAnalysisReportSerializer)
      self._event_object_serializer = (
          json_serializer.JSONEventObjectSerializer)
      self._event_tag_serializer = (
          json_serializer.JSONEventTagSerializer)
      self._pre_obj_serializer = (
          json_serializer.JSONPreprocessObjectSerializer)

    elif serializer_format == definitions.SERIALIZER_FORMAT_PROTOBUF:
      self._serializer_format_string = u'proto'

      self._analysis_report_serializer = (
          protobuf_serializer.ProtobufAnalysisReportSerializer)
      self._event_object_serializer = (
          protobuf_serializer.ProtobufEventObjectSerializer)
      self._event_tag_serializer = (
          protobuf_serializer.ProtobufEventTagSerializer)
      self._pre_obj_serializer = (
          protobuf_serializer.ProtobufPreprocessObjectSerializer)

    else:
      raise ValueError(
          u'Unsupported serializer format: {0:s}'.format(serializer_format))

  def _WritePreprocessObject(self, pre_obj):
    """Writes a preprocess object to the storage file.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).

    Raises:
      IOError: if the stream cannot be opened.
    """
    existing_stream_data = self._ReadStream(u'information.dump')

    # Store information about store range for this particular
    # preprocessing object. This will determine which stores
    # this information is applicable for.
    stores = self._GetSerializedEventObjectStreamNumbers()
    if stores:
      end = stores[-1] + 1
    else:
      end = self._first_file_number
    pre_obj.store_range = (self._first_file_number, end)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'pre_obj')

    pre_obj_data = self._pre_obj_serializer.WriteSerialized(pre_obj)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'pre_obj')

    stream_data = b''.join([
        existing_stream_data,
        struct.pack('<I', len(pre_obj_data)), pre_obj_data])

    self._WriteStream(u'information.dump', stream_data)

  def AddEventObject(self, event_object):
    """Adds an event object to the storage.

    Args:
      event_object: an event object (instance of EventObject).

    Raises:
      IOError: When trying to write to a closed storage file.
    """
    if not self._file_open:
      raise IOError(u'Trying to add an entry to a closed storage file.')

    if event_object.timestamp > self._buffer_last_timestamp:
      self._buffer_last_timestamp = event_object.timestamp

    # TODO: support negative timestamps.
    if (event_object.timestamp < self._buffer_first_timestamp and
        event_object.timestamp > 0):
      self._buffer_first_timestamp = event_object.timestamp

    attributes = event_object.GetValues()
    # Add values to counters.
    if self._pre_obj:
      self._pre_obj.counter[u'total'] += 1
      self._pre_obj.counter[attributes.get(u'parser', u'N/A')] += 1
      # TODO remove plugin, add parser chain. Refactor to separate method e.g.
      # UpdateEventCounters.
      if u'plugin' in attributes:
        self._pre_obj.plugin_counter[attributes.get(u'plugin', u'N/A')] += 1

    # Add to temporary counter.
    self._count_data_type[event_object.data_type] += 1
    parser = attributes.get(u'parser', u'unknown_parser')
    self._count_parser[parser] += 1

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'event_object')

    event_object_data = self._event_object_serializer.WriteSerialized(
        event_object)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'event_object')

    # TODO: Re-think this approach with the re-design of the storage.
    # Check if the event object failed to serialize (none is returned).
    if event_object_data is None:
      return

    heapq.heappush(
        self._buffer, (event_object.timestamp, event_object_data))
    self._buffer_size += len(event_object_data)
    self._write_counter += 1

    if self._buffer_size > self._max_buffer_size:
      self._FlushBuffer()

  def AddEventObjects(self, event_objects):
    """Adds event objects to the storage.

    Args:
      event_objects: a list or generator of event objects (instances of
                     EventObject).
    """
    for event_object in event_objects:
      self.AddEventObject(event_object)

  def Close(self):
    """Closes the storage, flush the last buffer and closes the ZIP file."""
    if self._file_open:
      if not self._read_only and self._pre_obj:
        self._WritePreprocessObject(self._pre_obj)

      self._FlushBuffer()
      self._zipfile.close()
      self._file_open = False
      if not self._read_only:
        logging.debug((
            u'[Storage] Closing the storage, number of events added: '
            u'{0:d}').format(self._write_counter))

    self._ProfilingStop()

  # TODO: move only used in testing.
  def GetGrouping(self):
    """Retrieves event groups.

    Yields:
      An event group protobuf object (instance of plaso_storage_pb2.EventGroup).

    Raises:
      IOError: if the event group data stream cannot be opened.
    """
    if not self.HasGrouping():
      return

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(u'plaso_grouping.'):
        continue

      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(self._zipfile, stream_name)

      event_group = self._ReadEventGroup(data_stream)
      while event_group:
        yield event_group
        event_group = self._ReadEventGroup(data_stream)

  def GetReports(self):
    """Retrieves the analysis reports.

    Yields:
      Analysis reports (instances of AnalysisReport).

    Raises:
      IOError: if the stream cannot be opened.
    """
    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(u'plaso_report.'):
        continue

      file_object = self._OpenStream(stream_name, u'r')
      if file_object is None:
        raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

      report_string = file_object.read(self.MAXIMUM_REPORT_PROTOBUF_SIZE)
      yield self._analysis_report_serializer.ReadSerialized(report_string)

  def GetSortedEntry(self):
    """Retrieves a sorted entry from the storage file.

    Returns:
      An event object (instance of EventObject).
    """
    if self._bound_first is None:
      self._bound_first, self._bound_last = (
          pfilter.TimeRangeCache.GetTimeRange())

    if self._merge_buffer is None:
      self._InitializeMergeBuffer()

    if not self._merge_buffer:
      return

    _, store_number, event_read = heapq.heappop(self._merge_buffer)
    if not event_read:
      return

    # Stop as soon as we hit the upper bound.
    if event_read.timestamp > self._bound_last:
      return

    new_event_object = self._GetEventObject(store_number)

    if new_event_object:
      heapq.heappush(
          self._merge_buffer,
          (new_event_object.timestamp, store_number, new_event_object))

    event_read.tag = self._ReadEventTagByIdentifier(
        event_read.store_number, event_read.store_index, event_read.uuid)

    return event_read

  def GetStorageInformation(self):
    """Retrieves storage (preprocessing) information stored in the storage file.

    Returns:
      A list of preprocessing objects (instances of PreprocessingObject)
      that contain the storage information.
    """
    stream_name = u'information.dump'
    if not self._HasStream(stream_name):
      return []

    data_stream = _SerializedDataStream(self._zipfile, stream_name)

    information = []
    preprocess_object = self._ReadPreprocessObject(data_stream)
    while preprocess_object:
      information.append(preprocess_object)
      preprocess_object = self._ReadPreprocessObject(data_stream)

    stores = self._GetSerializedEventObjectStreamNumbers()
    information[-1].stores = {}
    information[-1].stores[u'Number'] = len(stores)
    for store_number in stores:
      store_identifier = u'Store {0:d}'.format(store_number)
      information[-1].stores[store_identifier] = self._ReadMeta(store_number)

    return information

  # TODO: move only used in testing.
  def GetTagging(self):
    """Return a generator that reads all tagging information from storage.

    This function reads all tagging files inside the storage and returns
    back the EventTagging protobuf, and only that protobuf.

    Yields:
      All EventTag objects stored inside the storage container.

    Raises:
      IOError: if the stream cannot be opened.
    """
    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(u'plaso_tagging.'):
        continue

      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(self._zipfile, stream_name)

      event_tag = self._ReadEventTag(data_stream)
      while event_tag:
        yield event_tag
        event_tag = self._ReadEventTag(data_stream)

  def HasGrouping(self):
    """Return a bool indicating whether or not a Group file is stored."""
    for name in self._GetStreamNames():
      if name.startswith(u'plaso_grouping.'):
        return True
    return False

  def HasReports(self):
    """Return a bool indicating whether or not a Report file is stored."""
    for name in self._GetStreamNames():
      if name.startswith(u'plaso_report'):
        return True
    return False

  # TODO: move only used in testing.
  def HasTagging(self):
    """Return a bool indicating whether or not a Tag file is stored."""
    for name in self._GetStreamNames():
      if name.startswith(u'plaso_tagging.'):
        return True
    return False

  def SetEnableProfiling(self, enable_profiling, profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_type: optional profiling type. The default is 'all'.
    """
    self._enable_profiling = enable_profiling

    if self._enable_profiling:
      if (profiling_type in [u'all', u'serializers'] and
          not self._serializers_profiler):
        self._serializers_profiler = profiler.SerializersProfiler(u'Storage')

  def SetStoreLimit(self, unused_my_filter=None):
    """Set a limit to the stores used for returning data."""
    # Retrieve set first and last timestamps.
    self._bound_first, self._bound_last = pfilter.TimeRangeCache.GetTimeRange()

    self.store_range = []

    # TODO: Fetch a filter object from the filter query.

    for number in self._GetSerializedEventObjectStreamNumbers():
      # TODO: Read more criteria from here.
      first, last = self._ReadMeta(number).get(u'range', (0, limit.MAX_INT64))
      if last < first:
        logging.error(
            u'last: {0:d} first: {1:d} container: {2:d} (last < first)'.format(
                last, first, number))

      if first <= self._bound_last and self._bound_first <= last:
        # TODO: Check at least parser and data_type (stored in metadata).
        # Check whether these attributes exist in filter, if so use the filter
        # to determine whether the stores should be included.
        self.store_range.append(number)

      else:
        logging.debug(u'Store [{0:d}] not used'.format(number))

  # TODO: move only used in testing.
  def StoreGrouping(self, rows):
    """Store group information into the storage file.

    An EventGroup protobuf stores information about several
    EventObjects that belong to the same behavior or action. It can then
    be used to group similar events together to create a super event, or
    a higher level event.

    This function is used to store that information inside the storage
    file so it can be read later.

    The object that is passed in needs to have an iterator implemented
    and has to implement the following attributes (optional names within
    bracket)::

      name - The name of the grouped event.
      [description] - More detailed description of the event.
      [category] - If this group of events falls into a specific category.
      [color] - To highlight this particular group with a HTML color tag.
      [first_timestamp] - The first timestamp if applicable of the group.
      [last_timestamp] - The last timestamp if applicable of the group.
      events - A list of tuples (store_number and store_index of the
      EventObject protobuf that belongs to this group of events).

    Args:
      rows: An object that contains the necessary fields to construct
      an EventGroup. Has to be a generator object or an object that implements
      an iterator.
    """
    group_number = 1
    if self.HasGrouping():
      for name in self._GetStreamNames():
        if name.startswith(u'plaso_grouping.'):
          _, _, number_string = name.partition(u'.')
          try:
            number = int(number_string, 10)
            if number >= group_number:
              group_number = number + 1
          except ValueError:
            pass

    group_packed = []
    size = 0
    for row in rows:
      group = plaso_storage_pb2.EventGroup()
      group.name = row.name
      if hasattr(row, u'description'):
        group.description = utils.GetUnicodeString(row.description)
      if hasattr(row, u'category'):
        group.category = utils.GetUnicodeString(row.category)
      if hasattr(row, u'color'):
        group.color = utils.GetUnicodeString(row.color)

      for number, index in row.events:
        event_object = group.events.add()
        event_object.store_number = int(number)
        event_object.store_index = int(index)

      if hasattr(row, u'first_timestamp'):
        group.first_timestamp = int(row.first_timestamp)
      if hasattr(row, u'last_timestamp'):
        group.last_timestamp = int(row.last_timestamp)

      # TODO: implement event grouping.
      group_str = group.SerializeToString()
      packed = struct.pack('<I', len(group_str)) + group_str
      # TODO: Size is defined, should be used to determine if we've filled
      # our buffer size of group information. Check that and write a new
      # group store file in that case.
      size += len(packed)
      if size > self._max_buffer_size:
        logging.warning(u'Grouping has outgrown buffer size.')
      group_packed.append(packed)

    stream_name = u'plaso_grouping.{0:06d}'.format(group_number)
    self._WriteStream(stream_name, b''.join(group_packed))

  def StoreReport(self, analysis_report):
    """Store an analysis report.

    Args:
      analysis_report: An analysis report object (instance of AnalysisReport).
    """
    report_number = 1
    for name in self._GetStreamNames():
      if name.startswith(u'plaso_report.'):
        _, _, number_string = name.partition(u'.')
        try:
          number = int(number_string, 10)
        except ValueError:
          logging.error(u'Unable to read in report number.')
          number = 0
        if number >= report_number:
          report_number = number + 1

    stream_name = u'plaso_report.{0:06}'.format(report_number)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'analysis_report')

    serialized_report_proto = self._analysis_report_serializer.WriteSerialized(
        analysis_report)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'analysis_report')

    self._WriteStream(stream_name, serialized_report_proto)

  def StoreTagging(self, tags):
    """Store tag information into the storage file.

    Each EventObject can be tagged either manually or automatically
    to make analysis simpler, by providing more context to certain
    events or to highlight events for later viewing.

    The object passed in needs to be a list (or otherwise an iterator)
    that contains EventTag objects (event.EventTag).

    Args:
      tags: A list or an object providing an iterator that contains
      EventTag objects.

    Raises:
      IOError: if the stream cannot be opened.
    """
    if not self._pre_obj:
      self._pre_obj = event.PreprocessObject()

    if not hasattr(self._pre_obj, u'collection_information'):
      self._pre_obj.collection_information = {}

    self._pre_obj.collection_information[u'Action'] = u'Adding tags to storage.'
    self._pre_obj.collection_information[u'time_of_run'] = (
        timelib.Timestamp.GetNow())
    if not hasattr(self._pre_obj, u'counter'):
      self._pre_obj.counter = collections.Counter()

    tag_number = 1
    for name in self._GetStreamNames():
      if not name.startswith(u'plaso_tagging.'):
        continue

      _, _, number_string = name.partition(u'.')
      try:
        number = int(number_string, 10)
      except ValueError:
        continue

      if number >= tag_number:
        tag_number = number + 1
      if self._event_tag_index is None:
        self._BuildTagIndex()

    tag_packed = []
    tag_index = []
    size = 0
    for tag in tags:
      self._pre_obj.counter[u'Total Tags'] += 1
      if hasattr(tag, u'tags'):
        for tag_entry in tag.tags:
          self._pre_obj.counter[tag_entry] += 1

      if self._event_tag_index is not None:
        tag_index_value = self._event_tag_index.get(tag.string_key, None)
      else:
        tag_index_value = None

      # This particular event has already been tagged on a previous occasion,
      # we need to make sure we are appending to that particular tag.
      if tag_index_value is not None:
        stream_name = u'plaso_tagging.{0:06d}'.format(
            tag_index_value.store_number)

        if not self._HasStream(stream_name):
          raise IOError(u'No such stream: {0:s}'.format(stream_name))

        data_stream = _SerializedDataStream(self._zipfile, stream_name)
        # TODO: replace 0 by the actual event tag entry index.
        # This is for code consistency rather then a functional purpose.
        data_stream.SeekEntryAtOffset(0, tag_index_value.store_offset)

        # TODO: if old_tag is cached make sure to update cache after write.
        old_tag = self._ReadEventTag(data_stream)
        if not old_tag:
          continue

        # TODO: move the append functionality into EventTag.
        # Maybe name the function extend or update?
        if hasattr(old_tag, u'tags'):
          tag.tags.extend(old_tag.tags)

        if hasattr(old_tag, u'comment'):
          if hasattr(tag, u'comment'):
            tag.comment += old_tag.comment
          else:
            tag.comment = old_tag.comment

        if hasattr(old_tag, u'color') and not hasattr(tag, u'color'):
          tag.color = old_tag.color

      if self._serializers_profiler:
        self._serializers_profiler.StartTiming(u'event_tag')

      serialized_event_tag = self._event_tag_serializer.WriteSerialized(tag)

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'event_tag')

      # TODO: move to write class function of _EventTagIndexValue.
      packed = (
          struct.pack('<I', len(serialized_event_tag)) + serialized_event_tag)
      ofs = struct.pack('<I', size)
      if getattr(tag, u'store_number', 0):
        struct_string = (
            construct.Byte(u'type').build(1) + ofs +
            _EventTagIndexValue.TAG_STORE_STRUCT.build(tag))
      else:
        struct_string = (
            construct.Byte(u'type').build(2) + ofs +
            _EventTagIndexValue.TAG_UUID_STRUCT.build(tag))

      tag_index.append(struct_string)
      size += len(packed)
      tag_packed.append(packed)

    stream_name = u'plaso_tag_index.{0:06d}'.format(tag_number)
    self._WriteStream(stream_name, b''.join(tag_index))

    stream_name = u'plaso_tagging.{0:06d}'.format(tag_number)
    self._WriteStream(stream_name, b''.join(tag_packed))

    # TODO: Update the tags that have changed in the index instead
    # of flushing the index.

    # If we already built a list of tag in memory we need to clear that
    # since the tags have changed.
    if self._event_tag_index is not None:
      del self._event_tag_index
