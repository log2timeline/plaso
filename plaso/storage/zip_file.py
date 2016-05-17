# -*- coding: utf-8 -*-
"""The ZIP-based storage.

The ZIP-based storage can be described as a collection of storage files
(named streams) bundled in a single ZIP archive file.

There are multiple types of streams:
* metadata.txt
  Stream that contains the storage metadata.
* event_data.#
  The event data streams contain the serialized event objects.
* event_tag_data.#
  The event tag data streams contain the serialized event tag objects.
* event_index.#
  The event index streams contain the stream offset to the serialized
  event objects.
* event_tag_index.#
  The event tag index streams contain the stream offset to the serialized
  event tag objects.
* event_timestamps.#
  The event timestamps streams contain the timestamp of the serialized
  event objects.
* information.dump

The # in a stream name is referred to as the "store number". Streams with
the same prefix e.g. "event_" and "store number" are related.

+ The event data streams

The event data streams contain the serialized event objects. The serialized
events are stored in ascending timestamp order within an individual event data
stream. Note that the event data streams themselves are not ordered.

The event data streams were previously referred to as "proto files" because
historically the event data was serialized as protocol buffers (protobufs).

An event data stream consists of:
+------+-----------------+------+-...-+
| size | serialized data | size | ... |
+------+-----------------+------+-...-+

Where size is a 32-bit integer.

+ The event index stream

The event index streams contain the stream offset to the serialized event
objects stored in the corresponding event data stream.

An event data stream consists of an array of 32-bit integers:
+-----+-----+-...+
| int | int | ...|
+-----+-----+-...+

+ The event timestamps stream

The event timestamps streams contain the timestamp of the serialized
event objects.

An event data stream consists of an array of 64-bit integers:
+-----------+-----------+-...-+
| timestamp | timestamp | ... |
+-----------+-----------+-...-+

+ Version information

Deprecated in version 20160501:
* serializer.txt
  Stream that contains the serializer format.

Deprecated in version 20160502:
* plaso_index.#
  The event index streams contain the stream offset to the serialized
  event objects.
* plaso_proto.#
  The event data streams contain the serialized event objects.
* plaso_report.#
* plaso_tagging.#
  The event tag data streams contain the serialized event tag objects.
* plaso_tag_index.#
  The event tag index streams contain the stream offset to the serialized
  event tag objects.
* plaso_timestamps.#
  The event timestamps streams contain the timestamp of the serialized
  event objects.
"""

import collections
import heapq
import io
import logging
import os
import warnings
import zipfile

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error

import construct

from plaso.engine import profiler
from plaso.lib import definitions
from plaso.lib import errors
from plaso.serializer import json_serializer
from plaso.storage import reader
from plaso.storage import writer


class _EventsHeap(object):
  """Class that defines the event objects heap."""

  def __init__(self):
    """Initializes an event objects heap."""
    super(_EventsHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """The number of serialized event objects on the heap."""
    return len(self._heap)

  def PopEvent(self):
    """Pops an event object from the heap.

    Returns:
      A tuple containing an event object (instance of EventObject),
      an integer containing the number of the stream.
      If the heap is empty the values in the tuple will be None.
    """
    try:
      _, stream_number, _, event_object = heapq.heappop(self._heap)
      return event_object, stream_number

    except IndexError:
      return None, None

  def PushEvent(self, event_object, stream_number, entry_index):
    """Pushes an event object onto the heap.

    Args:
      event_object: an event object (instance of EventObject).
      stream_number: an integer containing the number of the stream.
      entry_index: an integer containing the serialized data stream entry index.
    """
    heap_values = (
        event_object.timestamp, stream_number, entry_index, event_object)
    heapq.heappush(self._heap, heap_values)


class _SerializedEventsHeap(object):
  """Class that defines the serialized event objects heap.

  Attributes:
    data_size: an integer containing the total data size of the serialized
               event objects on the heap.
  """

  def __init__(self):
    """Initializes a serialized event objects heap."""
    super(_SerializedEventsHeap, self).__init__()
    self._heap = []
    self.data_size = 0

  @property
  def number_of_events(self):
    """The number of serialized event objects on the heap."""
    return len(self._heap)

  def Empty(self):
    """Empties the heap."""
    self._heap = []
    self.data_size = 0

  def PopEvent(self):
    """Pops an event object from the heap.

    Returns:
      A tuple containing an integer containing the event timestamp and
      a binary string containing the serialized event object data.
      If the heap is empty the values in the tuple will be None.
    """
    try:
      timestamp, event_object_data = heapq.heappop(self._heap)

      self.data_size -= len(event_object_data)
      return timestamp, event_object_data

    except IndexError:
      return None, None

  def PushEvent(self, timestamp, event_object_data):
    """Pushes a serialized event object onto the heap.

    Args:
      timestamp: an integer containing the event timestamp.
      event_object_data: binary string containing the serialized
                         event object data.
    """
    heap_values = (timestamp, event_object_data)
    heapq.heappush(self._heap, heap_values)
    self.data_size += len(event_object_data)


class _EventTagIndexValue(object):
  """Class that defines the event tag index value.

  Arrtibutes:
    event_uuid: optional string containing the event identifier (UUID).
    offset: an integer containing the serialized event tag data offset.
    store_number: optional integer containing the store number.
    store_offset: optional integer containing the offset relative
                  to the start of the store.
    tag_type: an integer containing the tag type.
  """
  TAG_TYPE_UNDEFINED = 0
  TAG_TYPE_NUMERIC = 1
  TAG_TYPE_UUID = 2

  def __init__(
      self, tag_type, offset, event_uuid=None, store_number=None,
      store_offset=None):
    """Initializes the tag index value.

    Args:
      tag_type: an integer containing the tag type.
      offset: an integer containing the serialized event tag data offset.
      event_uuid: optional string containing the event identifier (UUID).
      store_number: optional integer containing the store number.
      store_offset: optional integer containing the offset relative
                    to the start of the store.
    """
    super(_EventTagIndexValue, self).__init__()
    self._identifier = None
    self.event_uuid = event_uuid
    self.offset = offset
    self.store_number = store_number
    self.store_offset = store_offset
    self.tag_type = tag_type

  def __str__(self):
    """Retrieve a string representation of the event tag identifier."""
    string = u'tag_type: {0:d} offset: 0x{1:08x}'.format(
        self.tag_type, self.offset)

    if self.tag_type == self.TAG_TYPE_NUMERIC:
      return u'{0:s} store_number: {1:d} store_offset: {2:d}'.format(
          string, self.store_number, self.store_offset)

    elif self.tag_type == self.TAG_TYPE_UUID:
      return u'{0:s} event_uuid: {1:s}'.format(string, self.event_uuid)

    return string

  @property
  def identifier(self):
    """A string containing the event object identifier."""
    if not self._identifier:
      if self.tag_type == self.TAG_TYPE_NUMERIC:
        self._identifier = u'{0:d}:{1:d}'.format(
            self.store_number, self.store_offset)

      elif self.tag_type == self.TAG_TYPE_UUID:
        self._identifier = self.event_uuid

    return self._identifier

  @property
  def tag(self):
    """The tag property to support construct.build()."""
    return self


class _SerializedDataStream(object):
  """Class that defines a serialized data stream."""

  _DATA_ENTRY = construct.Struct(
      u'data_entry',
      construct.ULInt32(u'size'))
  _DATA_ENTRY_SIZE = _DATA_ENTRY.sizeof()

  # The maximum serialized data size (40 MiB).
  _MAXIMUM_DATA_SIZE = 40 * 1024 * 1024

  def __init__(self, zip_file, storage_file_path, stream_name):
    """Initializes a serialized data stream object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      storage_file_path: string containing the path of the storage file.
      stream_name: string containing the name of the stream.
    """
    super(_SerializedDataStream, self).__init__()
    self._entry_index = 0
    self._file_object = None
    self._path = os.path.dirname(os.path.abspath(storage_file_path))
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
      self._file_object = self._zip_file.open(self._stream_name, mode='r')
    except KeyError as exception:
      raise IOError(
          u'Unable to open stream with error: {0:s}'.format(exception))

    self._stream_offset = 0

  def _ReOpenFileObject(self):
    """Reopens the file-like object (instance of ZipExtFile)."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

    self._file_object = self._zip_file.open(self._stream_name, mode='r')
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

  def WriteAbort(self):
    """Aborts the write of a serialized data stream."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

    if os.path.exists(self._stream_name):
      os.remove(self._stream_name)

  def WriteEntry(self, data):
    """Writes an entry to the file-like object.

    Args:
      data: a binary string containing the data.

    Returns:
      An integer containing the offset of the temporary file.

    Raises:
      IOError: if the entry cannot be written.
    """
    data_size = construct.ULInt32(u'size').build(len(data))
    self._file_object.write(data_size)
    self._file_object.write(data)

    return self._file_object.tell()

  def WriteFinalize(self):
    """Finalize the write of a serialized data stream.

    Writes the temporary file with the serialized data to the zip file.

    Returns:
      An integer containing the offset of the temporary file.

    Raises:
      IOError: if the serialized data stream cannot be written.
    """
    offset = self._file_object.tell()
    self._file_object.close()
    self._file_object = None

    current_working_directory = os.getcwd()
    try:
      os.chdir(self._path)
      self._zip_file.write(self._stream_name)
    finally:
      os.remove(self._stream_name)
      os.chdir(current_working_directory)

    return offset

  def WriteInitialize(self):
    """Initializes the write of a serialized data stream.

    Creates a temporary file to store the serialized data.

    Returns:
      An integer containing the offset of the temporary file.

    Raises:
      IOError: if the serialized data stream cannot be written.
    """
    stream_file_path = os.path.join(self._path, self._stream_name)
    self._file_object = open(stream_file_path, 'wb')
    return self._file_object.tell()


class _SerializedDataOffsetTable(object):
  """Class that defines a serialized data offset table."""

  _TABLE = construct.GreedyRange(
      construct.ULInt32(u'offset'))

  _TABLE_ENTRY = construct.Struct(
      u'table_entry',
      construct.ULInt32(u'offset'))
  _TABLE_ENTRY_SIZE = _TABLE_ENTRY.sizeof()

  def __init__(self, zip_file, stream_name):
    """Initializes a serialized data offset table object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      stream_name: string containing the name of the stream.
    """
    super(_SerializedDataOffsetTable, self).__init__()
    self._offsets = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  def AddOffset(self, offset):
    """Adds an offset.

    Args:
      offset: an integer containing the offset.
    """
    self._offsets.append(offset)

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
      file_object = self._zip_file.open(self._stream_name, mode='r')
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

  def Write(self):
    """Writes the offset table.

    Raises:
      IOError: if the offset table cannot be written.
    """
    table_data = self._TABLE.build(self._offsets)
    self._zip_file.writestr(self._stream_name, table_data)


class _SerializedDataTimestampTable(object):
  """Class that defines a serialized data timestamp table."""

  _TABLE = construct.GreedyRange(
      construct.SLInt64(u'timestamp'))

  _TABLE_ENTRY = construct.Struct(
      u'table_entry',
      construct.SLInt64(u'timestamp'))
  _TABLE_ENTRY_SIZE = _TABLE_ENTRY.sizeof()

  def __init__(self, zip_file, stream_name):
    """Initializes a serialized data timestamp table object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      stream_name: string containing the name of the stream.
    """
    super(_SerializedDataTimestampTable, self).__init__()
    self._timestamps = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  @property
  def number_of_timestamps(self):
    """The number of timestamps."""
    return len(self._timestamps)

  def AddTimestamp(self, timestamp):
    """Adds a timestamp.

    Args:
      timestamp: an integer containing the timestamp.
    """
    self._timestamps.append(timestamp)

  def GetTimestamp(self, entry_index):
    """Retrieves a specific timestamp.

    Args:
      entry_index: an integer containing the table entry index.

    Returns:
      An integer containing the timestamp.

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
      file_object = self._zip_file.open(self._stream_name, mode='r')
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

  def Write(self):
    """Writes the timestamp table.

    Raises:
      IOError: if the timestamp table cannot be written.
    """
    table_data = self._TABLE.build(self._timestamps)
    self._zip_file.writestr(self._stream_name, table_data)


class _SerializedEventTagIndexTable(object):
  """Class that defines a serialized event tag index table."""

  _TAG_STORE_STRUCT = construct.Struct(
      u'tag_store',
      construct.ULInt32(u'store_number'),
      construct.ULInt32(u'store_offset'))

  _TAG_UUID_STRUCT = construct.Struct(
      u'tag_uuid',
      construct.PascalString(u'event_uuid'))

  _TAG_INDEX_STRUCT = construct.Struct(
      u'tag_index',
      construct.Byte(u'tag_type'),
      construct.ULInt32(u'offset'),
      construct.IfThenElse(
          u'tag',
          lambda ctx: ctx[u'tag_type'] == 1,
          _TAG_STORE_STRUCT,
          _TAG_UUID_STRUCT))

  def __init__(self, zip_file, stream_name):
    """Initializes a serialized event tag index table object.

    Args:
      zip_file: the ZIP file object that contains the stream.
      stream_name: string containing the name of the stream.
    """
    super(_SerializedEventTagIndexTable, self).__init__()
    self._event_tag_indexes = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  @property
  def number_of_entries(self):
    """The number of event tag index entries."""
    return len(self._event_tag_indexes)

  def AddEventTagIndex(
      self, tag_type, offset, event_uuid=None, store_number=None,
      store_offset=None):
    """Adds an event tag index.

    Args:
      tag_type: an integer containing the tag type.
      offset: an integer containing the serialized event tag data offset.
      event_uuid: optional string containing the event identifier (UUID).
      store_number: optional integer containing the store number.
      store_offset: optional integer containing the offset relative
                    to the start of the store.
    """
    event_tag_index = _EventTagIndexValue(
        tag_type, offset, event_uuid=event_uuid, store_number=store_number,
        store_offset=store_offset)
    self._event_tag_indexes.append(event_tag_index)

  def GetEventTagIndex(self, entry_index):
    """Retrieves a specific event tag index.

    Args:
      entry_index: an integer containing the table entry index.

    Returns:
      An event tag index object (instance of _EventTagIndexValue).

    Raises:
      IndexError: if the table entry index is out of bounds.
    """
    return self._event_tag_indexes[entry_index]

  def Read(self):
    """Reads the serialized event tag index table.

    Raises:
      IOError: if the event tag index table cannot be read.
    """
    try:
      _, _, stream_store_number = self._stream_name.rpartition(u'.')
      stream_store_number = int(stream_store_number, 10)
    except ValueError as exception:
      raise IOError((
          u'Unable to determine store number of stream: {0:s} '
          u'with error: {1:s}').format(self._stream_name, exception))

    try:
      file_object = self._zip_file.open(self._stream_name, mode='r')
    except KeyError as exception:
      raise IOError(
          u'Unable to open stream with error: {0:s}'.format(exception))

    try:
      while True:
        try:
          tag_index_struct = self._TAG_INDEX_STRUCT.parse_stream(file_object)
        except (construct.FieldError, AttributeError):
          break

        tag_type = tag_index_struct.get(
            u'tag_type', _EventTagIndexValue.TAG_TYPE_UNDEFINED)
        if tag_type not in (
            _EventTagIndexValue.TAG_TYPE_NUMERIC,
            _EventTagIndexValue.TAG_TYPE_UUID):
          logging.warning(u'Unsupported tag type: {0:d}'.format(tag_type))
          break

        offset = tag_index_struct.get(u'offset', None)
        tag = tag_index_struct.get(u'tag', {})
        event_uuid = tag.get(u'event_uuid', None)
        store_number = tag.get(u'store_number', stream_store_number)
        store_offset = tag.get(u'store_offset', None)

        event_tag_index = _EventTagIndexValue(
            tag_type, offset, event_uuid=event_uuid, store_number=store_number,
            store_offset=store_offset)
        self._event_tag_indexes.append(event_tag_index)

    finally:
      file_object.close()

  def Write(self):
    """Writes the event tag index table.

    Raises:
      IOError: if the event tag index table cannot be written.
    """
    serialized_entries = []
    for event_tag_index in self._event_tag_indexes:
      entry_data = self._TAG_INDEX_STRUCT.build(event_tag_index)
      serialized_entries.append(entry_data)

    table_data = b''.join(serialized_entries)
    self._zip_file.writestr(self._stream_name, table_data)


class _StorageMetadata(object):
  """Class that implements storage metadata.

  Attributes:
    format_version: an integer containing the storage format version.
    serialization_format: a string containing the serialization format.
  """

  def __init__(self):
    """Initializes storage metadata."""
    super(_StorageMetadata, self).__init__()
    self.format_version = None
    self.serialization_format = None


class _StorageMetadataReader(object):
  """Class that implements a storage metadata reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser: the configuration parser (instance of ConfigParser).
      section_name: the name of the section that contains the value.
      value_name: the name of the value.

    Returns:
      An object containing the value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name).decode('utf-8')
    except (configparser.NoOptionError, configparser.NoSectionError):
      return

  def Read(self, stream_data):
    """Reads the storage metadata.

    Args:
      stream_data: a byte string containing the data of the steam.

    Returns:
      The storeage metadata (instance of _StorageMetadata).
    """
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(io.BytesIO(stream_data))

    section_name = u'plaso_storage_file'

    storage_metadata = _StorageMetadata()

    format_version = self._GetConfigValue(
        config_parser, section_name, u'format_version')

    try:
      storage_metadata.format_version = int(format_version, 10)
    except (TypeError, ValueError):
      storage_metadata.format_version = None

    storage_metadata.serialization_format = self._GetConfigValue(
        config_parser, section_name, u'serialization_format')

    return storage_metadata


class ZIPStorageFile(object):
  """Class that defines the ZIP-based storage file.

  This class contains the lower-level stream management functionality.

  The ZIP-based storage file contains several streams (files) that contain
  serialized attribute containers. E.g. event objects:

        event_data.#

  Where # is an increasing integer that starts at 1.
  """

  # The format version.
  _FORMAT_VERSION = 20160502

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _COMPATIBLE_FORMAT_VERSION = 20160501

  # The format version used for storage files predating storing
  # a format version.
  _LEGACY_FORMAT_VERSION = 20160431

  # The maximum number of cached tables.
  _MAXIMUM_NUMBER_OF_CACHED_TABLES = 5

  def __init__(self):
    """Initializes a ZIP-based storage file object."""
    super(ZIPStorageFile, self).__init__()
    self._event_offset_tables = {}
    self._event_offset_tables_lfu = []
    self._event_streams = {}
    self._event_timestamp_tables = {}
    self._event_timestamp_tables_lfu = []
    self._format_version = self._FORMAT_VERSION
    self._path = None
    self._zipfile = None

  def _Close(self):
    """Closes the storage file."""
    if not self._zipfile:
      return

    self._event_streams = {}
    self._event_offset_tables = {}
    self._event_offset_tables_lfu = []
    self._event_timestamp_tables = {}
    self._event_timestamp_tables_lfu = []

    self._zipfile.close()
    self._zipfile = None

  def _GetSerializedEventOffsetTable(self, stream_number):
    """Retrieves the serialized event object stream offset table.

    Args:
      stream_number: an integer containing the number of the stream.

    Returns:
      A serialized data offset table (instance of _SerializedDataOffsetTable).

    Raises:
      IOError: if the stream cannot be opened.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_index'
    else:
      stream_name_prefix = u'event_index'

    offset_table = self._event_offset_tables.get(stream_number, None)
    if not offset_table:
      stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)
      offset_table.Read()

      number_of_tables = len(self._event_offset_tables)
      if number_of_tables >= self._MAXIMUM_NUMBER_OF_CACHED_TABLES:
        lfu_stream_number = self._event_offset_tables_lfu.pop()
        del self._event_offset_tables[lfu_stream_number]

      self._event_offset_tables[stream_number] = offset_table

    if stream_number in self._event_offset_tables_lfu:
      lfu_index = self._event_offset_tables_lfu.index(stream_number)
      self._event_offset_tables_lfu.pop(lfu_index)

    self._event_offset_tables_lfu.append(stream_number)

    return offset_table

  def _GetSerializedEventStream(self, stream_number):
    """Retrieves the serialized event object stream.

    Args:
      stream_number: an integer containing the number of the stream.

    Returns:
      A serialized data stream object (instance of _SerializedDataStream).

    Raises:
      IOError: if the stream cannot be opened.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_proto'
    else:
      stream_name_prefix = u'event_data'

    data_stream = self._event_streams.get(stream_number, None)
    if not data_stream:
      stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._path, stream_name)
      self._event_streams[stream_number] = data_stream

    return data_stream

  def _GetSerializedEventTimestampTable(self, stream_number):
    """Retrieves the serialized event object stream timestamp table.

    Args:
      stream_number: an integer containing the number of the stream.

    Returns:
      A serialized data timestamp table (instance of
       _SerializedDataTimestampTable).

    Raises:
      IOError: if the stream cannot be opened.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_timestamps'
    else:
      stream_name_prefix = u'event_timestamps'

    timestamp_table = self._event_timestamp_tables.get(stream_number, None)
    if not timestamp_table:
      stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, stream_number)
      timestamp_table = _SerializedDataTimestampTable(
          self._zipfile, stream_name)
      timestamp_table.Read()

      number_of_tables = len(self._event_timestamp_tables)
      if number_of_tables >= self._MAXIMUM_NUMBER_OF_CACHED_TABLES:
        lfu_stream_number = self._event_timestamp_tables_lfu.pop()
        del self._event_timestamp_tables[lfu_stream_number]

      self._event_timestamp_tables[stream_number] = timestamp_table

    if stream_number in self._event_timestamp_tables_lfu:
      lfu_index = self._event_timestamp_tables_lfu.index(stream_number)
      self._event_timestamp_tables_lfu.pop(lfu_index)

    self._event_timestamp_tables_lfu.append(stream_number)

    return timestamp_table

  def _GetSerializedEventStreamNumbers(self):
    """Retrieves the available serialized event object stream numbers.

    Returns:
      A sorted list of integers of the available serialized data stream numbers.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_proto'
    else:
      stream_name_prefix = u'event_data'

    stream_numbers = []
    for stream_name in self._zipfile.namelist():
      if not stream_name.startswith(stream_name_prefix):
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

  def _Open(self, path, access_mode='r'):
    """Opens the storage file.

    Args:
      path: string containing the path of the storage file.
      access_mode: optional string indicating the access mode.

    Raises:
      IOError: if the ZIP file is already opened or if the ZIP file cannot
               be opened.
    """
    if self._zipfile:
      raise IOError(u'ZIP file already opened.')

    self._path = path

    try:
      self._zipfile = zipfile.ZipFile(
          self._path, mode=access_mode, compression=zipfile.ZIP_DEFLATED,
          allowZip64=True)

    except zipfile.BadZipfile as exception:
      raise IOError(
          u'Unable to open ZIP file with error: {0:s}'.format(exception))

  def _OpenStream(self, stream_name, access_mode='r'):
    """Opens a stream.

    Args:
      stream_name: string containing the name of the stream.
      access_mode: optional string indicating the access mode.

    Returns:
      The stream file-like object (instance of zipfile.ZipExtFile) or None.
    """
    try:
      return self._zipfile.open(stream_name, mode=access_mode)
    except KeyError:
      return

  def _ReadStream(self, stream_name):
    """Reads data from a stream.

    Args:
      stream_name: string containing the name of the stream.

    Returns:
      A byte string containing the data of the stream.
    """
    file_object = self._OpenStream(stream_name)
    if not file_object:
      return b''

    try:
      data = file_object.read()
    finally:
      file_object.close()

    return data

  def _WriteStream(self, stream_name, stream_data):
    """Writes data to a stream.

    Args:
      stream_name: a string containing the name of the stream.
      stream_data: a byte string containing the data of the steam.
    """
    # TODO: this can raise an IOError e.g. "Stale NFS file handle".
    # Determine if this be handled more error resiliently.

    # Prevent zipfile from generating "UserWarning: Duplicate name:".
    with warnings.catch_warnings():
      warnings.simplefilter(u'ignore')
      self._zipfile.writestr(stream_name, stream_data)


class StorageFile(ZIPStorageFile):
  """Class that defines the ZIP-based storage file."""

  # The maximum buffer size to 196 MiB.
  MAXIMUM_BUFFER_SIZE = 196 * 1024 * 1024

  # The maximum serialized report size to 24 MiB.
  MAXIMUM_SERIALIZED_REPORT_SIZE = 24 * 1024 * 1024

  def __init__(
      self, output_file, buffer_size=0, read_only=False,
      serializer_format=definitions.SERIALIZER_FORMAT_JSON):
    """Initializes the storage file.

    Args:
      output_file: a string containing the name of the output file.
      buffer_size: optional maximum size of a single storage file.
                   The default is 0, which indicates no limit.
      read_only: optional boolean to indicate we are opening the storage file
                 for reading only.
      serializer_format: optional storage serializer format.

    Raises:
      IOError: if we open the file in read only mode and the file does
               not exist.
    """
    super(StorageFile, self).__init__()
    self._analysis_report_serializer = None
    self._buffer = _SerializedEventsHeap()
    self._event_object_serializer = None
    self._event_tag_index = None
    self._file_number = 1
    self._first_file_number = None
    self._max_buffer_size = buffer_size or self.MAXIMUM_BUFFER_SIZE
    self._merge_buffer = None
    self._output_file = output_file
    self._preprocess_object_serializer = None
    self._read_only = read_only
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializer_format = serializer_format

    if self._read_only:
      access_mode = 'r'
    else:
      access_mode = 'a'

    self._Open(output_file, access_mode=access_mode)

    # Attributes for profiling.
    self._enable_profiling = False
    self._profiling_sample = 0
    self._serializers_profiler = None

  @property
  def file_path(self):
    """The file path."""
    return self._output_file

  @property
  def serialization_format(self):
    """The serialization format."""
    return self._serializer_format

  def _BuildTagIndex(self):
    """Builds the tag index that contains the offsets for each tag.

    Raises:
      IOError: if the stream cannot be opened.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_tag_index.'
    else:
      stream_name_prefix = u'event_tag_index.'

    self._event_tag_index = {}

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(stream_name_prefix):
        continue

      event_tag_index_table = _SerializedEventTagIndexTable(
          self._zipfile, stream_name)
      event_tag_index_table.Read()

      for entry_index in range(event_tag_index_table.number_of_entries):
        tag_index_value = event_tag_index_table.GetEventTagIndex(entry_index)
        self._event_tag_index[tag_index_value.identifier] = tag_index_value

  def _GetEventObject(self, stream_number, entry_index=-1):
    """Reads an event object from a specific stream.

    Args:
      stream_number: an integer containing the number of the serialized event
                     object stream.
      entry_index: an optional integer containing the number of the serialized
                   event object within the stream. Where -1 represents the next
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

    event_object = self._serializer.ReadSerialized(event_object_data)

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
      entry_index: an optional integer containing the number of the serialized
                   event object within the stream. Where -1 represents the next
                   available event object.

    Returns:
      A tuple containing the event object serialized data and the entry index
      of the event object within the storage file.

    Raises:
      IOError: if the stream cannot be opened.
    """
    try:
      data_stream = self._GetSerializedEventStream(stream_number)
    except IOError as exception:
      logging.error((
          u'Unable to retrieve serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    if entry_index >= 0:
      try:
        offset_table = self._GetSerializedEventOffsetTable(stream_number)
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

  def _InitializeMergeBuffer(self, time_range=None):
    """Initializes the event objects into the merge buffer.

    This function fills the merge buffer with the first relevant event object
    from each stream.

    Args:
      time_range: an optional time range object (instance of TimeRange).
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_timestamps'
    else:
      stream_name_prefix = u'event_timestamps'

    self._merge_buffer = _EventsHeap()

    number_range = self._GetSerializedEventStreamNumbers()
    for stream_number in number_range:
      entry_index = -1
      if time_range:
        stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, stream_number)
        if self._HasStream(stream_name):
          try:
            timestamp_table = self._GetSerializedEventTimestampTable(
                stream_number)
          except IOError as exception:
            logging.error((
                u'Unable to read timestamp table from stream: {0:s} '
                u'with error: {1:s}.').format(stream_name, exception))

          # If the start timestamp of the time range filter is larger than the
          # last timestamp in the timestamp table skip this stream.
          timestamp_compare = timestamp_table.GetTimestamp(-1)
          if time_range.start_timestamp > timestamp_compare:
            continue

          for table_index in range(timestamp_table.number_of_timestamps - 1):
            timestamp_compare = timestamp_table.GetTimestamp(table_index)
            if time_range.start_timestamp >= timestamp_compare:
              entry_index = table_index
              break

      event_object = self._GetEventObject(
          stream_number, entry_index=entry_index)
      # Check the lower bound in case no timestamp table was available.
      while (event_object and time_range and
             event_object.timestamp < time_range.start_timestamp):
        event_object = self._GetEventObject(stream_number)

      if event_object:
        if time_range and event_object.timestamp > time_range.end_timestamp:
          continue

        self._merge_buffer.PushEvent(
            event_object, stream_number, event_object.store_number)

        reference_timestamp = event_object.timestamp
        while event_object.timestamp == reference_timestamp:
          event_object = self._GetEventObject(stream_number)
          if not event_object:
            break

          self._merge_buffer.PushEvent(
              event_object, stream_number, event_object.store_number)

  def _Open(self, path, access_mode='r'):
    """Opens the storage file.

    Args:
      path: string containing the path of the storage file.
      access_mode: optional string indicating the access mode.

    Raises:
      IOError: if the file is opened in read only mode and the file does
               not exist or if the serializer format is not supported.
    """
    super(StorageFile, self)._Open(path, access_mode=access_mode)

    has_storage_metadata = self._ReadStorageMetadata()
    if not has_storage_metadata:
      # TODO: remove serializer.txt stream support in favor
      # of storage metatdata.
      logging.warning(u'Storage file does not contain a metadata stream.')

      stored_serializer_format = self._ReadSerializerStream()
      if stored_serializer_format:
        self._format_version = self._LEGACY_FORMAT_VERSION

        self._serializer_format = stored_serializer_format

    if self._serializer_format != definitions.SERIALIZER_FORMAT_JSON:
      raise IOError(u'Unsupported serializer format: {0:s}'.format(
          self._serializer_format))

    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._preprocess_object_serializer = (
        json_serializer.JSONPreprocessObjectSerializer)

    if access_mode != 'r':
      self._OpenWrite()

  def _OpenWrite(self):
    """Opens the storage file for writing."""
    logging.debug(u'Writing to ZIP file with buffer size: {0:d}'.format(
        self._max_buffer_size))

    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_proto.'
    else:
      stream_name_prefix = u'event_data.'

    # Determine the the last stream number.
    for stream_name in self._GetStreamNames():
      if stream_name.startswith(stream_name_prefix):
        _, _, file_number = stream_name.partition(u'.')

        try:
          file_number = int(file_number, 10)
          if file_number >= self._file_number:
            self._file_number = file_number + 1
        except ValueError:
          logging.warning((
              u'Found unsupported stream name: {0:s} while determining '
              u'the last storage number').format(stream_name))

    self._first_file_number = self._file_number

    if self._first_file_number == 1:
      self._WriteStorageMetadata()

  def _ProfilingStop(self):
    """Stops the profiling."""
    if self._serializers_profiler:
      self._serializers_profiler.Write()

  def _ReadAnalysisReport(self, data_stream):
    """Reads an analysis report.

    Args:
      data_stream: the data stream object (instance of _SerializedDataStream).

    Returns:
      An analysis report (instance of AnalysisReport) or None.
    """
    analysis_report_data = data_stream.ReadEntry()
    if not analysis_report_data:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'analysis_report')

    analysis_report = self._serializer.ReadSerialized(analysis_report_data)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'analysis_report')

    return analysis_report

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

    event_tag = self._serializer.ReadSerialized(event_tag_data)

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
      The event tag (instance of EventTag) or None.

    Raises:
      IOError: if the event tag data stream cannot be opened.
    """
    tag_index_value = self._GetEventTagIndexValue(
        store_number, entry_index, uuid)
    if tag_index_value is None:
      return

    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_tagging'
    else:
      stream_name_prefix = u'event_tag_data'

    stream_name = u'{0:s}.{1:06d}'.format(
        stream_name_prefix, tag_index_value.store_number)
    if not self._HasStream(stream_name):
      raise IOError(u'No such stream: {0:s}'.format(stream_name))

    data_stream = _SerializedDataStream(self._zipfile, self._path, stream_name)
    data_stream.SeekEntryAtOffset(entry_index, tag_index_value.store_offset)
    return self._ReadEventTag(data_stream)

  def _ReadPreprocessObject(self, data_stream):
    """Reads a preprocessing object.

    Args:
      data_stream: the data stream object (instance of _SerializedDataStream).

    Returns:
      An preprocessing object (instance of PreprocessObject) or None if the
      preprocessing object cannot be read.
    """
    preprocess_data = data_stream.ReadEntry()
    if not preprocess_data:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'preprocess_object')

    try:
      preprocess_object = self._preprocess_object_serializer.ReadSerialized(
          preprocess_data)
    except errors.SerializationError as exception:
      logging.error(exception)
      preprocess_object = None

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'preprocess_object')

    return preprocess_object

  def _ReadSerializerStream(self):
    """Reads the serializer stream.

    Note that the serializer stream has been deprecated in format version
    20160501 in favor of the the store metadata stream.

    Returns:
      The stored serializer format.

    Raises:
      ValueError: if the serializer format is not supported.
    """
    stream_name = u'serializer.txt'
    if not self._HasStream(stream_name):
      return

    serializer_format = self._ReadStream(stream_name)
    if serializer_format != definitions.SERIALIZER_FORMAT_JSON:
      raise ValueError(
          u'Unsupported stored serializer format: {0:s}'.format(
              serializer_format))

    return serializer_format

  def _ReadStorageMetadata(self):
    """Reads the storage metadata.

    Returns:
      A boolean value to indicate if the storage metadata was read.

    Raises:
      IOError: if the format version or the serializer format is not supported.
    """
    stream_name = u'metadata.txt'
    if not self._HasStream(stream_name):
      return False

    storage_metadata_reader = _StorageMetadataReader()
    stream_data = self._ReadStream(stream_name)
    storage_metadata = storage_metadata_reader.Read(stream_data)

    if not storage_metadata.format_version:
      raise IOError(u'Missing format version.')

    if storage_metadata.format_version < self._COMPATIBLE_FORMAT_VERSION:
      raise IOError(
          u'Format version: {0:d} is too old and no longer supported.'.format(
              storage_metadata.format_version))

    if storage_metadata.format_version > self._FORMAT_VERSION:
      raise IOError(
          u'Format version: {0:d} is too new and not yet supported.'.format(
              storage_metadata.format_version))

    serialization_format = storage_metadata.serialization_format
    if serialization_format != definitions.SERIALIZER_FORMAT_JSON:
      raise IOError(
          u'Unsupported serialization format: {0:s}'.format(
              serialization_format))

    self._format_version = storage_metadata.format_version
    self._serializer_format = serialization_format

    return True

  def _WriteBuffer(self):
    """Writes the buffered event objects to the storage file."""
    if not self._buffer.data_size:
      return

    stream_name = u'event_index.{0:06d}'.format(self._file_number)
    offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)

    stream_name = u'event_timestamps.{0:06d}'.format(self._file_number)
    timestamp_table = _SerializedDataTimestampTable(self._zipfile, stream_name)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    stream_name = u'event_data.{0:06d}'.format(self._file_number)
    data_stream = _SerializedDataStream(self._zipfile, self._path, stream_name)
    entry_data_offset = data_stream.WriteInitialize()
    try:
      for _ in range(0, self._buffer.number_of_events):
        timestamp, entry_data = self._buffer.PopEvent()

        timestamp_table.AddTimestamp(timestamp)
        offset_table.AddOffset(entry_data_offset)

        entry_data_offset = data_stream.WriteEntry(entry_data)

    except:
      data_stream.WriteAbort()

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'write')

      raise

    offset_table.Write()
    data_stream.WriteFinalize()
    timestamp_table.Write()

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'write')

    self._file_number += 1
    self._buffer.Empty()

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    stream_name = u'metadata.txt'
    if self._HasStream(stream_name):
      return

    stream_data = (
        b'[plaso_storage_file]\n'
        b'format_version: {0:d}\n'
        b'serialization_format: {1:s}\n'
        b'\n').format(self._FORMAT_VERSION, self._serializer_format)

    self._WriteStream(stream_name, stream_data)

  def AddEventObject(self, event_object):
    """Adds an event object to the storage.

    Args:
      event_object: an event object (instance of EventObject).

    Raises:
      IOError: when trying to write to a closed storage file.
    """
    if not self._zipfile:
      raise IOError(u'Trying to add an entry to a closed storage file.')

    # We try to serialize the event object first, so we can skip some
    # processing if it's invalid.
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'event_object')
    try:
      event_object_data = self._serializer.WriteSerialized(event_object)
      # TODO: Re-think this approach with the re-design of the storage.
      # Check if the event object failed to serialize (none is returned).
      if event_object_data is None:
        return
    except UnicodeDecodeError:
      error_message = (
          u'Unicode error while serializing event. It will be excluded from '
          u'output. Details: Event: "{0:s}" data type: "{1:s}" '
          u'parser: "{2:s}"').format(
              event_object.uuid, event_object.data_type, event_object.parser)
      logging.error(error_message)
      return
    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'event_object')

    self._buffer.PushEvent(event_object.timestamp, event_object_data)

    if self._buffer.data_size > self._max_buffer_size:
      self._WriteBuffer()

  def Close(self):
    """Closes the storage, flush the last buffer and closes the ZIP file."""
    if not self._zipfile:
      return

    if not self._read_only:
      number_of_events = self._buffer.number_of_events

      self._WriteBuffer()

      logging.debug((
          u'[Storage] Closing the storage, number of events added: '
          u'{0:d}').format(number_of_events))

    self._Close()

    self._ProfilingStop()

  def GetReports(self):
    """Retrieves the analysis reports.

    Yields:
      Analysis reports (instances of AnalysisReport).

    Raises:
      IOError: if the stream cannot be opened.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_report.'
    else:
      stream_name_prefix = u'analysis_report_data.'

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(stream_name_prefix):
        continue

      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      if self._format_version <= 20160501:
        file_object = self._OpenStream(stream_name)
        if file_object is None:
          raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

        report_string = file_object.read(self.MAXIMUM_SERIALIZED_REPORT_SIZE)
        yield self._serializer.ReadSerialized(report_string)

      else:
        data_stream = _SerializedDataStream(
            self._zipfile, self._path, stream_name)

        analysis_report = self._ReadAnalysisReport(data_stream)
        while analysis_report:
          yield analysis_report
          analysis_report = self._ReadAnalysisReport(data_stream)

  def GetSortedEntry(self, time_range=None):
    """Retrieves a sorted entry.

    Args:
      time_range: an optional time range object (instance of TimeRange).

    Returns:
      An event object (instance of EventObject).
    """
    if not self._merge_buffer:
      self._InitializeMergeBuffer(time_range=time_range)
      if not self._merge_buffer:
        return

    event_object, stream_number = self._merge_buffer.PopEvent()
    if not event_object:
      return

    # Stop as soon as we hit the upper bound.
    if time_range and event_object.timestamp > time_range.end_timestamp:
      return

    next_event_object = self._GetEventObject(stream_number)
    if next_event_object:
      self._merge_buffer.PushEvent(
          next_event_object, stream_number, event_object.store_index)

      reference_timestamp = next_event_object.timestamp
      while next_event_object.timestamp == reference_timestamp:
        next_event_object = self._GetEventObject(stream_number)
        if not next_event_object:
          break

        self._merge_buffer.PushEvent(
            next_event_object, stream_number, event_object.store_index)

    event_object.tag = self._ReadEventTagByIdentifier(
        event_object.store_number, event_object.store_index, event_object.uuid)

    return event_object

  def GetStorageInformation(self):
    """Retrieves storage (preprocessing) information stored in the storage file.

    Returns:
      A list of preprocessing objects (instances of PreprocessingObject)
      that contain the storage information.
    """
    stream_name = u'information.dump'
    if not self._HasStream(stream_name):
      return []

    data_stream = _SerializedDataStream(self._zipfile, self._path, stream_name)

    information = []
    preprocess_object = self._ReadPreprocessObject(data_stream)
    while preprocess_object:
      information.append(preprocess_object)
      preprocess_object = self._ReadPreprocessObject(data_stream)

    return information

  def GetTagging(self):
    """Retrieves the event tags.

    Yields:
      An event tag object (instance of EventTag).

    Raises:
      IOError: if the stream cannot be opened.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_tagging.'
    else:
      stream_name_prefix = u'event_tag_data.'

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(stream_name_prefix):
        continue

      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._path, stream_name)

      event_tag = self._ReadEventTag(data_stream)
      while event_tag:
        yield event_tag
        event_tag = self._ReadEventTag(data_stream)

  def HasReports(self):
    """Determines if a storage file contains reports.

    Returns:
      A boolean value indicating if the storage file contains reports.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_report.'
    else:
      stream_name_prefix = u'analysis_report_data.'

    for name in self._GetStreamNames():
      if name.startswith(stream_name_prefix):
        return True

    return False

  def HasTagging(self):
    """Determines if a storage file contains event tags.

    Returns:
      A boolean value indicating if the storage file contains event tags.
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_tagging.'
    else:
      stream_name_prefix = u'event_tag_data.'

    for name in self._GetStreamNames():
      if name.startswith(stream_name_prefix):
        return True

    return False

  def SetEnableProfiling(self, enable_profiling, profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_type: optional profiling type.
    """
    self._enable_profiling = enable_profiling

    if self._enable_profiling:
      if (profiling_type in [u'all', u'serializers'] and
          not self._serializers_profiler):
        self._serializers_profiler = profiler.SerializersProfiler(u'Storage')

  def StoreReport(self, analysis_report):
    """Store an analysis report.

    Args:
      analysis_report: an analysis report object (instance of AnalysisReport).
    """
    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_report.'
    else:
      stream_name_prefix = u'analysis_report_data.'

    report_number = 1
    for name in self._GetStreamNames():
      if name.startswith(stream_name_prefix):

        _, _, number_string = name.partition(u'.')
        try:
          number = int(number_string, 10)
        except ValueError:
          logging.error(u'Unable to read in report number.')
          number = 0
        if number >= report_number:
          report_number = number + 1

    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_report'
    else:
      stream_name_prefix = u'analysis_report_data'

    stream_name = u'{0:s}.{1:06}'.format(stream_name_prefix, report_number)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'analysis_report')

    serialized_report = self._serializer.WriteSerialized(analysis_report)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'analysis_report')

    if self._format_version <= 20160501:
      self._WriteStream(stream_name, serialized_report)
    else:
      data_stream = _SerializedDataStream(
          self._zipfile, self._path, stream_name)
      data_stream.WriteInitialize()
      data_stream.WriteEntry(serialized_report)
      data_stream.WriteFinalize()

  def StoreTagging(self, tags):
    """Store tag information into the storage file.

    Each EventObject can be tagged either manually or automatically
    to make analysis simpler, by providing more context to certain
    events or to highlight events for later viewing.

    The object passed in needs to be a list (or otherwise an iterator)
    that contains event tag objects.

    Args:
      tags: a list of event tags (instances of EventTag).

    Raises:
      IOError: if the stream cannot be opened.
    """
    tag_number = 1
    for name in self._GetStreamNames():
      if self._format_version <= 20160501:
        stream_name_prefix = u'plaso_tagging.'
      else:
        stream_name_prefix = u'event_tag_data.'

      if not name.startswith(stream_name_prefix):
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

    serialized_event_tags = []
    for tag in tags:
      if self._event_tag_index is not None:
        tag_index_value = self._event_tag_index.get(tag.string_key, None)
      else:
        tag_index_value = None

      # This particular event has already been tagged on a previous occasion,
      # we need to make sure we are appending to that particular tag.
      if tag_index_value is not None:
        if self._format_version <= 20160501:
          stream_name_prefix = u'plaso_tagging'
        else:
          stream_name_prefix = u'event_tag_data'

        stream_name = u'{0:s}.{1:06d}'.format(
            stream_name_prefix, tag_index_value.store_number)

        if not self._HasStream(stream_name):
          raise IOError(u'No such stream: {0:s}'.format(stream_name))

        data_stream = _SerializedDataStream(
            self._zipfile, self._path, stream_name)
        # TODO: replace 0 by the actual event tag entry index.
        # This is for code consistency rather then a functional purpose.
        data_stream.SeekEntryAtOffset(0, tag_index_value.offset)

        # TODO: if old_tag is cached make sure to update cache after write.
        old_tag = self._ReadEventTag(data_stream)
        if not old_tag:
          continue

        tag.AddComment(old_tag.comment)
        tag.AddLabels(old_tag.labels)

      if self._serializers_profiler:
        self._serializers_profiler.StartTiming(u'event_tag')

      serialized_event_tag = self._serializer.WriteSerialized(tag)

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'event_tag')

      serialized_event_tags.append(serialized_event_tag)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_tag_index'
    else:
      stream_name_prefix = u'event_tag_index'

    stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, tag_number)
    event_tag_index_table = _SerializedEventTagIndexTable(
        self._zipfile, stream_name)

    if self._format_version <= 20160501:
      stream_name_prefix = u'plaso_tagging'
    else:
      stream_name_prefix = u'event_tag_data'

    stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, tag_number)
    data_stream = _SerializedDataStream(self._zipfile, self._path, stream_name)
    entry_data_offset = data_stream.WriteInitialize()

    try:
      for tag_index, tag in enumerate(tags):
        entry_data_offset = data_stream.WriteEntry(
            serialized_event_tags[tag_index])

        event_uuid = getattr(tag, u'event_uuid', None)
        store_number = getattr(tag, u'store_number', None)
        store_offset = getattr(tag, u'store_index', None)

        if event_uuid:
          tag_type = _EventTagIndexValue.TAG_TYPE_UUID
        else:
          tag_type = _EventTagIndexValue.TAG_TYPE_NUMERIC

        event_tag_index_table.AddEventTagIndex(
            tag_type, entry_data_offset, event_uuid=event_uuid,
            store_number=store_number, store_offset=store_offset)

    except:
      data_stream.WriteAbort()

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'write')

      raise

    event_tag_index_table.Write()
    data_stream.WriteFinalize()

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'write')

    # TODO: Update the tags that have changed in the index instead
    # of flushing the index.

    # If we already built a list of tag in memory we need to clear that
    # since the tags have changed.
    if self._event_tag_index is not None:
      del self._event_tag_index

  def WritePreprocessObject(self, preprocess_object):
    """Writes a preprocess object to the storage file.

    Args:
      preprocess_object: the preprocess object (instance of PreprocessObject).

    Raises:
      IOError: if the stream cannot be opened.
    """
    existing_stream_data = self._ReadStream(u'information.dump')

    # Store information about store range for this particular
    # preprocessing object. This will determine which stores
    # this information is applicable for.
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'preprocess_object')

    preprocess_object_data = (
        self._preprocess_object_serializer.WriteSerialized(preprocess_object))

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'preprocess_object')

    # TODO: use _SerializedDataStream.
    preprocess_object_data_size = construct.ULInt32(u'size').build(
        len(preprocess_object_data))
    stream_data = b''.join([
        existing_stream_data, preprocess_object_data_size,
        preprocess_object_data])

    self._WriteStream(u'information.dump', stream_data)


class ZIPStorageFileReader(reader.StorageReader):
  """Class that implements the ZIP-based storage file reader."""

  def __init__(self, zip_storage_file):
    """Initializes a storage reader object.

    Args:
      zip_storage_file: a ZIP-based storage file (instance of ZIPStorageFile).
    """
    super(ZIPStorageFileReader, self).__init__()
    self._zip_storage_file = zip_storage_file

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self._zip_storage_file.Close()

  def GetEvents(self, time_range=None):
    """Retrieves events.

    Args:
      time_range: an optional time range object (instance of TimeRange).

    Yields:
      An event object (instance of EventObject).
    """
    event_object = self._zip_storage_file.GetSortedEntry(
        time_range=time_range)

    while event_object:
      yield event_object
      event_object = self._zip_storage_file.GetSortedEntry(
          time_range=time_range)


class ZIPStorageFileWriter(writer.StorageWriter):
  """Class that implements the ZIP-based storage file writer."""

  def __init__(
      self, event_object_queue, output_file, preprocess_object,
      buffer_size=0, serializer_format=definitions.SERIALIZER_FORMAT_JSON):
    """Initializes a storage writer object.

    Args:
      event_object_queue: an event object queue (instance of Queue).
      output_file: a string containing the path to the output file.
      preprocess_object: a preprocess object (instance of PreprocessObject).
      buffer_size: optional integer containing the estimated size of
                   a protobuf file.
      serializer_format: optional storage serializer format.
    """
    super(ZIPStorageFileWriter, self).__init__(event_object_queue)
    self._buffer_size = buffer_size
    self._output_file = output_file
    # Counter containing the number of events per parser.
    self._parsers_counter = collections.Counter()
    # Counter containing the number of events per parser plugin.
    self._plugins_counter = collections.Counter()
    self._preprocess_object = preprocess_object
    self._serializer_format = serializer_format
    self._storage_file = None

  def _Close(self):
    """Closes the storage writer."""
    # TODO: move the counters out of preprocessing object.
    # Kept for backwards compatibility for now.
    self._preprocess_object.counter = self._parsers_counter
    self._preprocess_object.plugin_counter = self._plugins_counter

    self._storage_file.WritePreprocessObject(self._preprocess_object)

    self._storage_file.Close()

  def _ConsumeItem(self, event_object, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      event_object: an event object (instance of EventObject).
    """
    self._storage_file.AddEventObject(event_object)
    self._UpdateCounters(event_object)

  def _Open(self):
    """Opens the storage writer."""
    self._storage_file = StorageFile(
        self._output_file, buffer_size=self._buffer_size,
        serializer_format=self._serializer_format)

    self._storage_file.SetEnableProfiling(
        self._enable_profiling, profiling_type=self._profiling_type)

  def _UpdateCounters(self, event_object):
    """Updates the counters.

    Args:
      event_object: an event object (instance of EventObject).
    """
    self._parsers_counter[u'total'] += 1

    parser_name = getattr(event_object, u'parser', u'N/A')
    self._parsers_counter[parser_name] += 1

    # TODO: remove plugin, add parser chain.
    if hasattr(event_object, u'plugin'):
      plugin_name = getattr(event_object, u'plugin', u'N/A')
      self._plugins_counter[plugin_name] += 1
