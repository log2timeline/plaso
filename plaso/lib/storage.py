#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The storage mechanism.

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

Simple text file using YAML for storing metadata information about the store.
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
import construct
import heapq
import logging
# TODO: replace all instances of struct by construct!
import struct
import sys
import zipfile

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import limit
from plaso.lib import pfilter
from plaso.lib import output
from plaso.lib import queue
from plaso.lib import timelib
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer

from google.protobuf import message
import yaml


class _EventTagIndexValue(object):
  """Class that defines the event tag index value."""

  TAG_STORE_STRUCT = construct.Struct(
      'tag_store',
      construct.ULInt32('store_number'),
      construct.ULInt32('store_index'))

  TAG_UUID_STRUCT = construct.Struct(
      'tag_uuid',
      construct.PascalString('event_uuid'))

  TAG_INDEX_STRUCT = construct.Struct(
      'tag_index',
      construct.Byte('type'),
      construct.ULInt32('offset'),
      construct.IfThenElse(
          'tag',
          lambda ctx: ctx['type'] == 1,
          TAG_STORE_STRUCT,
          TAG_UUID_STRUCT))

  TAG_TYPE_UNDEFINED = 0
  TAG_TYPE_NUMERIC = 1
  TAG_TYPE_UUID = 2

  def __init__(self, identifier, store_number=0, store_offset=0):
    """Initializes the tag index value.

    Args:
      identifier: the identifier string.
      store_number: optional store number. The default is 0.
      store_offset: optional offset relative to the start of the store.
                    The default 0.
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

    tag_type = tag_index_struct.get('type', cls.TAG_TYPE_UNDEFINED)
    if tag_type not in [cls.TAG_TYPE_NUMERIC, cls.TAG_TYPE_UUID]:
      logging.warning('Unsupported tag type: {0:d}'.format(tag_type))
      return None

    tag_entry = tag_index_struct.get('tag', {})
    if tag_type == cls.TAG_TYPE_NUMERIC:
      tag_identifier = '{}:{}'.format(
          tag_entry.get('store_number', 0),
          tag_entry.get('store_index', 0))

    else:
      tag_identifier = tag_entry.get('event_uuid', '0')

    store_offset = tag_index_struct.get('offset')
    return _EventTagIndexValue(
        tag_identifier, store_number=store_number, store_offset=store_offset)


class StorageFile(object):
  """Class that defines the storage file."""

  _STREAM_DATA_SEGMENT_SIZE = 1024

  # Set the maximum buffer size to 196 MiB
  MAX_BUFFER_SIZE = 196 * 1024 * 1024

  # Set the maximum protobuf string size to 40 MiB
  MAX_PROTO_STRING_SIZE = 40 * 1024 * 1024

  # Set the maximum report protobuf string size to 24 MiB
  MAX_REPORT_PROTOBUF_SIZE = 24 * 1024 * 1024

  # Set the version of this storage mechanism.
  STORAGE_VERSION = 1

  # Define structs.
  INTEGER = construct.ULInt32('integer')

  source_short_map = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      'SourceShort'].values:
    source_short_map[value.name] = value.number

  def __init__(
      self, output_file, buffer_size=0, read_only=False, pre_obj=None):
    """Initializes the storage file.

    Args:
      output_file: The name of the output file.
      buffer_size: The estimated size of a protobuf file.
      read_only: Indicate we are just opening up ZIP file for reading.
      pre_obj: A preprocessing object that gets stored inside the storage
      if defined.

    Raises:
      IOError: if we open up the file in read only mode and the file does
      not exist.
    """
    compression = zipfile.ZIP_DEFLATED

    # TODO: set self._bound_first and remove the hasattr checks for
    # a true of false evaluation.
    self._buffer = []
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0
    self._buffer_size = 0
    self._event_tag_index = None
    self._filenumber = 1
    self._max_buffer_size = buffer_size or self.MAX_BUFFER_SIZE
    self._pre_obj = pre_obj
    self._proto_streams = {}
    self._read_only = read_only
    self._write_counter = 0

    self._analysis_report_serializer = (
        protobuf_serializer.ProtobufAnalysisReportSerializer)
    self._event_object_serializer = (
        protobuf_serializer.ProtobufEventObjectSerializer)
    self._event_tag_serializer = (
        protobuf_serializer.ProtobufEventTagSerializer)
    self._pre_obj_serializer = (
        protobuf_serializer.ProtobufPreprocessObjectSerializer)

    if read_only:
      mode = 'r'
    else:
      mode = 'a'

    try:
      self._zipfile = zipfile.ZipFile(output_file, mode, compression)
    except zipfile.BadZipfile as e:
      raise IOError(u'Unable to read ZIP file with error: {0:s}'.format(e))
    self._file_open = True

    if not read_only:
      logging.debug(u'Writing to ZIP file with buffer size: {0:d}'.format(
          self._max_buffer_size))

      if pre_obj:
        pre_obj.counter = collections.Counter()
        pre_obj.plugin_counter = collections.Counter()
        if hasattr(pre_obj, 'collection_information'):
          cmd_line = ' '.join(sys.argv)
          encoding = getattr(pre_obj, 'preferred_encoding', None)
          if encoding:
            try:
              cmd_line = cmd_line.decode(encoding)
            except UnicodeDecodeError:
              pass
          pre_obj.collection_information['cmd_line'] = cmd_line

      # Start up a counter for modules in buffer.
      self._count_data_type = collections.Counter()
      self._count_parser = collections.Counter()

      # Need to get the last number in the list.
      for stream_name in self._GetStreamNames():
        if stream_name.startswith('plaso_meta.'):
          _, _, file_number = stream_name.partition('.')

          try:
            file_number = int(file_number, 10)
            if file_number >= self._filenumber:
              self._filenumber = file_number + 1
          except ValueError:
            # Ignore invalid metadata stream names.
            pass

      self._first_filenumber = self._filenumber

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def _BuildTagIndex(self):
    """Builds the tag index that contains the offsets for each tag.

    Raises:
      IOError: if the stream cannot be opened.
    """
    self._event_tag_index = {}

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith('plaso_tag_index.'):
        continue

      file_object = self._OpenStream(stream_name, 'r')
      if file_object is None:
        raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

      _, _, store_number = stream_name.rpartition('.')
      # TODO: catch exception.
      store_number = int(store_number, 10)

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
        'range': (self._buffer_first_timestamp, self._buffer_last_timestamp),
        'version': self.STORAGE_VERSION,
        'data_type': list(self._count_data_type.viewkeys()),
        'parsers': list(self._count_parser.viewkeys()),
        'count': len(self._buffer),
        'type_count': self._count_data_type.most_common()}
    self._count_data_type = collections.Counter()
    self._count_parser = collections.Counter()

    stream_name = 'plaso_meta.{0:06d}'.format(self._filenumber)
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
      index_str.append(struct.pack('<I', ofs))
      timestamp_str.append(struct.pack('<q', timestamp))
      packed = struct.pack('<I', len(entry)) + entry
      ofs += len(packed)
      proto_str.append(packed)

    stream_name = 'plaso_index.{0:06d}'.format(self._filenumber)
    self._WriteStream(stream_name, ''.join(index_str))

    stream_name = 'plaso_proto.{0:06d}'.format(self._filenumber)
    self._WriteStream(stream_name, ''.join(proto_str))

    stream_name = 'plaso_timestamps.{0:06d}'.format(self._filenumber)
    self._WriteStream(stream_name, ''.join(timestamp_str))

    self._filenumber += 1
    self._buffer_size = 0
    self._buffer = []
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0

  def _GetEventTagIndexValue(self, store_number, store_index, uuid):
    """Retrieves an event tag index value.

    Args:
      store_number: the store number.
      store_index: the store index.
      uuid: the UUID string.

    Returns:
      An event tag index value (instance of _EventTagIndexValue).
    """
    if self._event_tag_index is None:
      self._BuildTagIndex()

    # Try looking up event tag by numeric identifier.
    tag_identifier = '{0:d}:{1:d}'.format(store_number, store_index)
    tag_index_value = self._event_tag_index.get(tag_identifier, None)

    # Try looking up event tag by UUID.
    if tag_index_value is None:
      tag_index_value = self._event_tag_index.get(uuid, None)

    return tag_index_value

  def _GetStreamNames(self):
    """Retrieves a generator of the storage stream names."""
    if self._zipfile:
      for stream_name in self._zipfile.namelist():
        yield stream_name

  def _GetEventObjectProtobufString(self, stream_number, entry_index=-1):
    """Returns a specific event object protobuf string.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      stream_number: The proto stream number.
      entry_index: Read a specific entry in the file, otherwise the next one.

    Returns:
      A tuple containing the event object protobuf string and the entry index
      of the event object protobuf string within the storage file.

    Raises:
      EOFError: When we reach the end of the protobuf file.
      errors.WrongProtobufEntry: If the probotuf size is too large for storage.
      IOError: if the stream cannot be opened.
    """
    file_object, last_entry_index = self._GetProtoStream(stream_number)

    if entry_index >= 0:
      stream_offset = self._GetProtoStreamOffset(stream_number, entry_index)
      if stream_offset is None:
        logging.error((
            u'Unable to read entry index: {0:d} from proto stream: '
            u'{1:d}').format(entry_index, stream_number))

        return None, None

      file_object, last_entry_index = self._GetProtoStreamSeekOffset(
          stream_number, entry_index, stream_offset)

    if (not last_entry_index and hasattr(self, '_bound_first')
        and self._bound_first and entry_index == -1):
      # We only get here if the following conditions are met:
      #   1. last_entry_index is not set (so this is the first read
      #      from this file).
      #   2. There is a lower bound (so we have a date filter).
      #   3. The lower bound is higher than zero (basically set to a value).
      #   4. We are accessing this function using 'get me the next entry' as an
      #      opposed to the 'get me entry X', where we just want to server entry
      #      X.
      #
      # The purpose: speed seeking into the storage file based on time. Instead
      # of spending precious time reading through the storage file and
      # deserializing protobufs just to compare timestamps we read a much
      # 'cheaper' file, one that only contains timestamps to find the proper
      # entry into the storage file. That way we'll get to the right place in
      # the file and can start reading protobufs from the right location.
      index = 0

      # TODO: why is the stream name set here but not used? Is this a left over?
      stream_name = 'plaso_timestamps.{0:06d}'.format(stream_number)

      # Recent add-on to the storage file, not certain this file exists.
      if stream_name in self._GetStreamNames():
        timestamp_file_object = self._OpenStream(stream_name, 'r')
        if timestamp_file_object is None:
          raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

        timestamp_compare = 0
        while timestamp_compare < self._bound_first:
          timestamp_raw = timestamp_file_object.read(8)
          if len(timestamp_raw) != 8:
            break
          timestamp_compare = struct.unpack('<q', timestamp_raw)[0]
          index += 1
        return self._GetEventObjectProtobufString(stream_number, index)

    size_data = file_object.read(4)

    if len(size_data) != 4:
      return None, None

    proto_string_size = struct.unpack('<I', size_data)[0]

    if proto_string_size > self.MAX_PROTO_STRING_SIZE:
      raise errors.WrongProtobufEntry(
          u'Protobuf string size value exceeds maximum: {0:d}'.format(
              proto_string_size))

    event_object_data = file_object.read(proto_string_size)
    self._proto_streams[stream_number] = (file_object, last_entry_index + 1)

    return event_object_data, last_entry_index

  def _GetEventGroupProto(self, file_object):
    """Return a single group entry."""
    unpacked = file_object.read(4)
    if len(unpacked) != 4:
      return None

    size = struct.unpack('<I', unpacked)[0]

    if size > StorageFile.MAX_PROTO_STRING_SIZE:
      raise errors.WrongProtobufEntry(
          u'Protobuf size too large: {0:d}'.format(size))

    proto_serialized = file_object.read(size)
    proto = plaso_storage_pb2.EventGroup()

    proto.ParseFromString(proto_serialized)
    return proto

  def _GetProtoStream(self, stream_number):
    """Retrieves the proto stream.

    Args:
      stream_number: the number of the stream.

    Returns:
      A tuple of the stream file-like object and the last entry index to
      which the offset of the stream file-like object points.

    Raises:
      IOError: if the stream cannot be opened.
    """
    if stream_number not in self._proto_streams:
      stream_name = 'plaso_proto.{0:06d}'.format(stream_number)

      file_object = self._OpenStream(stream_name, 'r')
      if file_object is None:
        raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

      # TODO: change this to a value object and track the stream offset as well.
      # This allows to reduce the number of re-opens when the seek offset is
      # beyond the current offset.
      self._proto_streams[stream_number] = (file_object, 0)

    return self._proto_streams[stream_number]

  def _GetProtoStreamSeekOffset(
      self, stream_number, entry_index, stream_offset):
    """Retrieves the proto stream and seeks a specified offset in the stream.

    Args:
      stream_number: the number of the stream.
      entry_index: the entry index.
      stream_offset: the offset relative to the start of the stream.

    Returns:
      A tuple of the stream file-like object and the last index.

    Raises:
      IOError: if the stream cannot be opened.
    """
    # Since zipfile.ZipExtFile is not seekable we need to close the stream
    # and reopen it to fake a seek.
    if stream_number in self._proto_streams:
      previous_file_object, _ = self._proto_streams[stream_number]
      del self._proto_streams[stream_number]
      previous_file_object.close()

    stream_name = 'plaso_proto.{0:06d}'.format(stream_number)
    file_object = self._OpenStream(stream_name, 'r')
    if file_object is None:
      raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

    # Since zipfile.ZipExtFile is not seekable we need to read upto
    # the stream offset.
    _ = file_object.read(stream_offset)

    self._proto_streams[stream_number] = (file_object, entry_index)

    return self._proto_streams[stream_number]

  def _GetProtoStreamOffset(self, stream_number, entry_index):
    """Retrieves the offset of a proto stream entry from the index stream.

    Args:
      stream_number: the number of the stream.
      entry_index: the entry index.

    Returns:
      The offset of the entry in the corresponding proto stream
      or None on error.

    Raises:
      IOError: if the stream cannot be opened.
    """
    # TODO: cache the index file object in the same way as the proto
    # stream file objects.

    # TODO: once cached use the last entry index to determine if the stream
    # file object should be re-opened.

    stream_name = 'plaso_index.{0:06d}'.format(stream_number)
    index_file_object = self._OpenStream(stream_name, 'r')
    if index_file_object is None:
      raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

    # Since zipfile.ZipExtFile is not seekable we need to read upto
    # the stream offset.
    _ = index_file_object.read(entry_index * 4)

    index_data = index_file_object.read(4)

    index_file_object.close()

    if len(index_data) != 4:
      return None

    return struct.unpack('<I', index_data)[0]

  def _OpenStream(self, stream_name, mode='r'):
    """Opens a stream.

    Args:
      stream_name: the name of the stream.
      mode: the access mode. The default is read-only ('r').

    Returns:
      The stream file-like object (instance of zipfile.ZipExtFile) or None.
    """
    try:
      return self._zipfile.open(stream_name, mode)
    except KeyError:
      return

  def _ReadEventTag(self, file_object):
    """Reads an event tag from the storage file.

    Returns:
      An event tag (instance of EventTag).
    """
    event_tag_data = file_object.read(4)
    if len(event_tag_data) != 4:
      return None

    proto_string_size = self.INTEGER.parse(event_tag_data)

    if proto_string_size > self.MAX_PROTO_STRING_SIZE:
      raise errors.WrongProtobufEntry(
          u'Protobuf string size value exceeds maximum: {0:d}'.format(
              proto_string_size))

    proto_string = file_object.read(proto_string_size)
    return self._event_tag_serializer.ReadSerialized(proto_string)

  def _ReadEventTagByIdentifier(self, store_number, store_index, uuid):
    """Reads an event tag by identifier.

    Args:
      store_number: the store number.
      store_index: the store index.
      uuid: the UUID string.

    Returns:
      The event tag (instance of EventTag).

    Raises:
      IOError: if the stream cannot be opened.
    """
    tag_index_value = self._GetEventTagIndexValue(
        store_number, store_index, uuid)
    if tag_index_value is None:
      return

    stream_name = 'plaso_tagging.{0:06d}'.format(tag_index_value.store_number)
    tag_file_object = self._OpenStream(stream_name, 'r')
    if tag_file_object is None:
      raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

    # Since zipfile.ZipExtFile is not seekable we need to read upto
    # the store offset.
    _  = tag_file_object.read(tag_index_value.store_offset)
    return self._ReadEventTag(tag_file_object)

  def _ReadStream(self, stream_name):
    """Reads the data in a stream.

    Args:
      stream_name: the name of the stream.

    Returns:
      A byte string containing the data of the stream.
    """
    data_segments = []
    file_object = self._OpenStream(stream_name, 'r')

    # zipfile.ZipExtFile does not support the with-statement interface.
    if file_object:
      data = file_object.read(self._STREAM_DATA_SEGMENT_SIZE)
      while data:
        data_segments.append(data)
        data = file_object.read(self._STREAM_DATA_SEGMENT_SIZE)

      file_object.close()

    return ''.join(data_segments)

  def _WritePreprocessObject(self, pre_obj):
    """Writes a preprocess object to the storage file.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).

    Raises:
      IOError: if the stream cannot be opened.
    """
    existing_stream_data = self._ReadStream('information.dump')

    # Store information about store range for this particular
    # preprocessing object. This will determine which stores
    # this information is applicaple for.
    stores = list(self.GetProtoNumbers())
    if stores:
      end = stores[-1] + 1
    else:
      end = self._first_filenumber
    pre_obj.store_range = (self._first_filenumber, end)

    pre_obj_data = self._pre_obj_serializer.WriteSerialized(pre_obj)

    stream_data = ''.join([
        existing_stream_data,
        struct.pack('<I', len(pre_obj_data)), pre_obj_data])

    self._WriteStream('information.dump', stream_data)

  def _WriteStream(self, stream_name, stream_data):
    """Write the data to a stream.

    Args:
      stream_name: the name of the stream.
      stream_data: the data of the steam.
    """
    self._zipfile.writestr(stream_name, stream_data)

  def Close(self):
    """Closes the storage, flush the last buffer and closes the ZIP file."""
    if self._file_open:
      if self._pre_obj:
        self._WritePreprocessObject(self._pre_obj)

      self._FlushBuffer()
      self._zipfile.close()
      self._file_open = False
      if not self._read_only:
        logging.info((
            u'[Storage] Closing the storage, number of events processed: '
            u'{0:d}').format(self._write_counter))

  def GetGrouping(self):
    """Return a generator that reads all grouping information from storage.

    Raises:
      IOError: if the stream cannot be opened.
    """
    if not self.HasGrouping():
      return

    for stream_name in self._GetStreamNames():
      if stream_name.startswith('plaso_grouping.'):
        file_object = self._OpenStream(stream_name, 'r')
        if file_object is None:
          raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

        group_entry = self._GetEventGroupProto(file_object)
        while group_entry:
          yield group_entry
          group_entry = self._GetEventGroupProto(file_object)

  def GetNumberOfEvents(self):
    """Retrieves the number of event objects in a storage file."""
    total_events = 0
    if hasattr(self, 'GetStorageInformation'):
      for store_info in self.GetStorageInformation():
        if hasattr(store_info, 'stores'):
          stores = store_info.stores.values()
          for store_file in stores:
            if type(store_file) is dict and 'count' in store_file:
              total_events += store_file['count']

    return total_events

  def GetEventsFromGroup(self, group_proto):
    """Return a generator with all EventObjects from a group."""
    for group_event in group_proto.events:
      yield self.GetEventObject(
          group_event.store_number, group_event.store_index)

  def GetTagging(self):
    """Return a generator that reads all tagging information from storage.

    This function reads all tagging files inside the storage and returns
    back the EventTagging protobuf, and only that protobuf.

    To get the full EventObject with tags attached it is possible to use
    the GetTaggedEvent and pass the EventTagging protobuf to it.

    Yields:
      All EventTag objects stored inside the storage container.

    Raises:
      IOError: if the stream cannot be opened.
    """
    for stream_name in self._GetStreamNames():
      if stream_name.startswith('plaso_tagging.'):
        file_object = self._OpenStream(stream_name, 'r')
        if file_object is None:
          raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

        tag_entry = self._ReadEventTag(file_object)
        while tag_entry:
          yield tag_entry
          tag_entry = self._ReadEventTag(file_object)

  def GetTaggedEvent(self, tag_event):
    """Read in an EventTag object from a tag and return an EventObject.

    This function uses the information inside the EventTag object
    to open the EventObject that was tagged and returns it, with the
    tag information attached to it.

    Args:
      tag_event: An EventTag object.

    Returns:
      An EventObject with the EventTag object attached.
    """
    evt = self.GetEventObject(tag_event.store_number, tag_event.store_index)
    if not evt:
      return None

    evt.tag = tag_event

    return evt

  def GetProtoEntry(self, stream_number, entry_index=-1):
    """Return an EventObject protobuf.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      stream_number: The proto stream number.
      entry_index: Read a specific entry in the file, otherwise the next one.

    Returns:
      An event protobuf (EventObject) entry read from the file.
    """
    event_object_data, entry_index = self._GetEventObjectProtobufString(
        stream_number, entry_index)
    if not event_object_data:
      return None

    proto = plaso_storage_pb2.EventObject()
    proto.ParseFromString(event_object_data)
    proto.store_number = stream_number
    proto.store_index = entry_index

    return proto

  def GetStorageInformation(self):
    """Return gathered preprocessing information from a storage file."""
    information = []

    file_object = self._OpenStream('information.dump', 'r')
    if file_object is None:
      return information

    while True:
      unpacked = file_object.read(4)
      if len(unpacked) != 4:
        break

      size = struct.unpack('<I', unpacked)[0]

      if size > self.MAX_PROTO_STRING_SIZE:
        raise errors.WrongProtobufEntry(
            u'Protobuf size too large: {0:d}'.format(size))

      serialized_pre_obj = file_object.read(size)
      try:
        info = self._pre_obj_serializer.ReadSerialized(serialized_pre_obj)
      except message.DecodeError:
        logging.error(u'Unable to parse preprocessing object, bailing out.')
        break

      information.append(info)

    stores = list(self.GetProtoNumbers())
    information[-1].stores = {}
    information[-1].stores['Number'] = len(stores)
    for store_number in stores:
      store_identifier = 'Store {0:d}'.format(store_number)
      information[-1].stores[store_identifier] = self.ReadMeta(store_number)

    return information

  def SetStoreLimit(self, unused_my_filter=None):
    """Set a limit to the stores used for returning data."""
    # We are setting the bounds now, remove potential prior bound settings.
    if hasattr(self, '_bound_first'):
      del self._bound_first

    self.store_range = []

    # Retrieve set first and last timestamps.
    self._GetTimeBounds()

    # TODO: Fetch a filter object from the filter query.

    for number in self.GetProtoNumbers():
      # TODO: Read more criteria from here.
      first, last = self.ReadMeta(number).get('range', (0, limit.MAX_INT64))
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

  def _GetTimeBounds(self):
    """Get the upper and lower time bounds."""
    if hasattr(self, '_bound_first'):
      return

    self._bound_first, self._bound_last = pfilter.TimeRangeCache.GetTimeRange()

  def GetSortedEntry(self, proto_out=False):
    """Return a sorted entry from the storage file.

    Args:
      proto_out: A boolean variable indicating whether or not a protobuf
      or a python object should be returned.

    Returns:
      An EventObject python object, unless proto_out is set then an EventObject
      protobuf is returned back.
    """
    if not hasattr(self, '_bound_first'):
      self._GetTimeBounds()

    if not hasattr(self, '_merge_buffer'):
      self._merge_buffer = []
      number_range = getattr(self, 'store_range', list(self.GetProtoNumbers()))
      for store_number in number_range:
        if proto_out:
          event_object = self.GetProtoEntry(store_number)
          if not event_object:
            return
          while event_object.timestamp < self._bound_first:
            event_object = self.GetProtoEntry(store_number)
            if not event_object:
              return
        else:
          event_object = self.GetEventObject(store_number)
          if not event_object:
            return
          while event_object.timestamp < self._bound_first:
            event_object = self.GetEventObject(store_number)
            if not event_object:
              return

        heapq.heappush(
            self._merge_buffer,
            (event_object.timestamp, store_number, event_object))

    if not self._merge_buffer:
      return

    _, store_number, event_read = heapq.heappop(self._merge_buffer)
    if not event_read:
      return

    # Stop as soon as we hit the upper bound.
    if event_read.timestamp > self._bound_last:
      return

    if proto_out:
      new_event_object = self.GetProtoEntry(store_number)
    else:
      new_event_object = self.GetEventObject(store_number)

    if new_event_object:
      heapq.heappush(
          self._merge_buffer,
          (new_event_object.timestamp, store_number, new_event_object))

    event_read.tag = self._ReadEventTagByIdentifier(
        event_read.store_number, event_read.store_index, event_read.uuid)

    return event_read

  def GetEventObject(self, stream_number, entry_index=-1):
    """Reads an event object from the store.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      stream_number: The proto stream number.
      entry_index: Read a specific entry in the file, otherwise the next one.

    Returns:
      An event object (EventObject) entry read from the file.
    """
    event_object_data, entry_index = self._GetEventObjectProtobufString(
        stream_number, entry_index)
    if not event_object_data:
      return None

    event_object = self._event_object_serializer.ReadSerialized(
        event_object_data)
    event_object.store_number = stream_number
    event_object.store_index = entry_index

    return event_object

  def GetEntries(self, number):
    """A generator to read all plaso_storage protobufs.

    The storage mechanism of Plaso works in the way that it creates potentially
    several files inside the ZIP container. As soon as the number of protobufs
    stored exceed the size of buffer_size they will be flushed to disk as:

          plaso_proto.XXX

    Where XXX is an increasing integer, starting from one. To get all the files
    or the numbers that are available this class implements a method called
    GetProtoNumbers() that returns a list of all available protobuf files within
    the container.

    This method returns a generator that returns all plaso_storage protobufs in
    the named container, as indicated by the number argument. So if this method
    is called as storage_object.GetEntries(1) the generator will return the
    entries found in the file plaso_proto.000001.

    Args:
      number: The protofile number.

    Yields:
      A protobuf object from the protobuf file.
    """
    # TODO: Change this function, don't accespt a store number and implement the
    # MergeSort functionailty of the psort file in here. This will then always
    # return the sorted entries from the storage file, implementing the second
    # stage of the sort/merge algorithm.
    while True:
      try:
        proto = self.GetEventObject(number)
        if not proto:
          logging.debug(
              u'End of protobuf file plaso_proto.{0:06d} reached.'.format(
                  number))
          break
        yield proto
      except errors.WrongProtobufEntry as e:
        logging.warning((
            u'Problem while parsing a protobuf entry from: '
            u'plaso_proto.{0:06d} <{1:s}>').format(number, e))

  def GetProtoNumbers(self):
    """Return all available protobuf numbers."""
    numbers = []
    for name in self._GetStreamNames():
      if 'plaso_proto' in name:
        _, num = name.split('.')
        numbers.append(int(num))

    for number in sorted(numbers):
      yield number

  def ReadMeta(self, number):
    """Return a dict with the metadata entries.

    Args:
      number: The number of the metadata file (name is plaso_meta_XXX where
              XXX is this number.

    Returns:
      A dict object containing all the variables inside the metadata file.

    Raises:
      IOError: if the stream cannot be opened.
    """
    stream_name = 'plaso_meta.{0:06d}'.format(number)
    file_object = self._OpenStream(stream_name, 'r')
    if file_object is None:
      raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))
    return yaml.safe_load(file_object)

  def GetBufferSize(self):
    """Return the size of the buffer."""
    return self._buffer_size

  def GetFileNumber(self):
    """Return the current file number of the storage."""
    return self._filenumber

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

    # Add values to counters.
    if self._pre_obj:
      self._pre_obj.counter['total'] += 1
      self._pre_obj.counter[event_object.attributes.get('parser', 'N/A')] += 1
      if 'plugin' in event_object.GetAttributes():
        self._pre_obj.plugin_counter[getattr(event_object, 'plugin')] += 1

    # Add to temporary counter.
    self._count_data_type[event_object.data_type] += 1
    parser = event_object.attributes.get('parser', 'unknown_parser')
    self._count_parser[parser] += 1

    event_object_data = self._event_object_serializer.WriteSerialized(
        event_object)

    heapq.heappush(
        self._buffer, (event_object.timestamp, event_object_data))
    self._buffer_size += len(event_object_data)
    self._write_counter += 1

    if self._buffer_size > self._max_buffer_size:
      self._FlushBuffer()

  def AddEventObjects(self, event_objects):
    """Adds an event objects to the storage.

    Args:
      event_objects: a list or generator of event objects (instances of
                     EventObject).
    """
    for event_object in event_objects:
      self.AddEventObject(event_object)

  def HasTagging(self):
    """Return a bool indicating whether or not a Tag file is stored."""
    for name in self._GetStreamNames():
      if 'plaso_tagging.' in name:
        return True
    return False

  def HasGrouping(self):
    """Return a bool indicating whether or not a Group file is stored."""
    for name in self._GetStreamNames():
      if 'plaso_grouping.' in name:
        return True
    return False

  def HasReports(self):
    """Return a bool indicating whether or not a Report file is stored."""
    for name in self._GetStreamNames():
      if 'plaso_report.' in name:
        return True

    return False

  def StoreReport(self, analysis_report):
    """Store an analysis report.

    Args:
      analysis_report: An analysis report object (instance of AnalysisReport).
    """
    report_number = 1
    for name in self._GetStreamNames():
      if 'plaso_report.' in name:
        _, _, number_string = name.partition('.')
        try:
          number = int(number_string, 10)
        except ValueError:
          logging.error(u'Unable to read in report number.')
          number = 0
        if number >= report_number:
          report_number = number + 1

    stream_name = 'plaso_report.{0:06}'.format(report_number)
    serialized_report_proto = self._analysis_report_serializer.WriteSerialized(
        analysis_report)
    self._WriteStream(stream_name, serialized_report_proto)

  def GetReports(self):
    """Read in all stored analysis reports from storage and yield them.

    Raises:
      IOError: if the stream cannot be opened.
    """
    for stream_name in self._GetStreamNames():
      if stream_name.startswith('plaso_report.'):
        file_object = self._OpenStream(stream_name, 'r')
        if file_object is None:
          raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

        report_string = file_object.read(self.MAX_REPORT_PROTOBUF_SIZE)
        yield self._analysis_report_serializer.ReadSerialized(report_string)

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
    bracket):
      name - The name of the grouped event.
      [description] - More detailed description of the event.
      [category] - If this group of events falls into a specific category.
      [color] - To highlight this particular group with a HTML color tag.
      [first_timestamp] - The first timestamp if applicaple of the group.
      [last_timestamp] - The last timestamp if applicaple of the group.
      events - A list of tuples (store_number and store_index of the
      EventObject protobuf that belongs to this group of events).

    Args:
      rows: An object that contains the necessary fields to contruct
      an EventGroup. Has to be a generator object or an object that implements
      an iterator.
    """
    group_number = 1
    if self.HasGrouping():
      for name in self._GetStreamNames():
        if 'plaso_grouping.' in name:
          _, number = name.split('.')
          if int(number) >= group_number:
            group_number = int(number) + 1

    group_packed = []
    size = 0
    for row in rows:
      group = plaso_storage_pb2.EventGroup()
      group.name = row.name
      if hasattr(row, 'description'):
        group.description = utils.GetUnicodeString(row.description)
      if hasattr(row, 'category'):
        group.category = utils.GetUnicodeString(row.category)
      if hasattr(row, 'color'):
        group.color = utils.GetUnicodeString(row.color)

      for number, index in row.events:
        evt = group.events.add()
        evt.store_number = int(number)
        evt.store_index = int(index)

      if hasattr(row, 'first_timestamp'):
        group.first_timestamp = int(row.first_timestamp)
      if hasattr(row, 'last_timestamp'):
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

    stream_name = 'plaso_grouping.{0:06d}'.format(group_number)
    self._WriteStream(stream_name, ''.join(group_packed))

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

    if not hasattr(self._pre_obj, 'collection_information'):
      self._pre_obj.collection_information = {}

    self._pre_obj.collection_information['Action'] = 'Adding tags to storage.'
    self._pre_obj.collection_information['time_of_run'] = (
        timelib.Timestamp.GetNow())
    if not hasattr(self._pre_obj, 'counter'):
      self._pre_obj.counter = collections.Counter()

    tag_number = 1
    for name in self._GetStreamNames():
      if 'plaso_tagging.' in name:
        _, number = name.split('.')
        if int(number) >= tag_number:
          tag_number = int(number) + 1
        if self._event_tag_index is None:
          self._BuildTagIndex()

    tag_packed = []
    tag_index = []
    size = 0
    for tag in tags:
      self._pre_obj.counter['Total Tags'] += 1
      if hasattr(tag, 'tags'):
        for tag_entry in tag.tags:
          self._pre_obj.counter[tag_entry] += 1

      if self._event_tag_index is not None:
        tag_index_value = self._event_tag_index.get(tag.string_key, None)
      else:
        tag_index_value = None

      # This particular event has already been tagged on a previous occasion,
      # we need to make sure we are appending to that particular tag.
      if tag_index_value is not None:
        stream_name = 'plaso_tagging.{0:06d}'.format(
            tag_index_value.store_number)

        tag_file_object = self._OpenStream(stream_name, 'r')
        if tag_file_object is None:
          raise IOError(u'Unable to open stream: {0:s}'.format(stream_name))

        # Since zipfile.ZipExtFile is not seekable we need to read upto
        # the store offset.
        _ = tag_file_object.read(tag_index_value.store_offset)

        old_tag = self._ReadEventTag(tag_file_object)

        # TODO: move the append functionality into EventTag.
        # Maybe name the function extend or update?
        if hasattr(old_tag, 'tags'):
          tag.tags.extend(old_tag.tags)

        if hasattr(old_tag, 'comment'):
          if hasattr(tag, 'comment'):
            tag.comment += old_tag.comment
          else:
            tag.comment = old_tag.comment

        if hasattr(old_tag, 'color') and not hasattr(tag, 'color'):
          tag.color = old_tag.color

      serialized_event_tag = self._event_tag_serializer.WriteSerialized(tag)

      # TODO: move to write class function of _EventTagIndexValue.
      packed = (
          struct.pack('<I', len(serialized_event_tag)) + serialized_event_tag)
      ofs = struct.pack('<I', size)
      if getattr(tag, 'store_number', 0):
        struct_string = (
            construct.Byte('type').build(1) + ofs +
            _EventTagIndexValue.TAG_STORE_STRUCT.build(tag))
      else:
        struct_string = (
            construct.Byte('type').build(2) + ofs +
            _EventTagIndexValue.TAG_UUID_STRUCT.build(tag))

      tag_index.append(struct_string)
      size += len(packed)
      tag_packed.append(packed)

    stream_name = 'plaso_tag_index.{0:06d}'.format(tag_number)
    self._WriteStream(stream_name, ''.join(tag_index))

    stream_name = 'plaso_tagging.{0:06d}'.format(tag_number)
    self._WriteStream(stream_name, ''.join(tag_packed))

    # TODO: Update the tags that have changed in the index instead
    # of flushing the index.

    # If we already built a list of tag in memory we need to clear that
    # since the tags have changed.
    if self._event_tag_index is not None:
      del self._event_tag_index


class StorageFileWriter(queue.EventObjectQueueConsumer):
  """Class that implements a storage file writer object."""

  def __init__(self, storage_queue, output_file, buffer_size=0, pre_obj=None):
    """Initializes the storage file writer.

    Args:
      storage_queue: the storage queue (instance of Queue).
      output_file: The path to the output file.
      buffer_size: The estimated size of a protobuf file.
      pre_obj: A preprocessing object (instance of PreprocessObject).
    """
    super(StorageFileWriter, self).__init__(storage_queue)
    self._buffer_size = buffer_size
    self._output_file = output_file
    self._pre_obj = pre_obj
    self._storage_file = None

  def _ConsumeEventObject(self, event_object):
    """Consumes an event object callback for ConsumeEventObjects."""
    self._storage_file.AddEventObject(event_object)

  def WriteEventObjects(self):
    """Writes the event objects that are pushed on the queue."""
    self._storage_file = StorageFile(
        self._output_file, buffer_size=self._buffer_size, pre_obj=self._pre_obj)
    self.ConsumeEventObjects()
    self._storage_file.Close()


class BypassStorageWriter(queue.EventObjectQueueConsumer):
  """Watch a queue with EventObjects and send them directly to output."""

  def __init__(
      self, storage_queue, output_file, output_module_string='lst2csv',
      pre_obj=None):
    """Initializes the bypass storage writer.

    Args:
      storage_queue: the storage queue (instance of Queue).
      output_file: The path to the output file.
      output_module_string: The output module string.
      pre_obj: A preprocessing object (instance of PreprocessObject).
    """
    super(BypassStorageWriter, self).__init__(storage_queue)
    self._output_file = output_file
    self._output_module = None
    self._output_module_string = output_module_string
    self._pre_obj = pre_obj
    self._pre_obj.store_range = (1, 1)

  def _ConsumeEventObject(self, event_object):
    """Consumes an event object callback for ConsumeEventObjects."""
    # Set the store number and index to default values since they are not used.
    event_object.store_number = 1
    event_object.store_index = -1

    self._output_module.WriteEvent(event_object)

  # Typically you will have a storage object that has this function,
  # as in you can call store.GetStorageInformation and that will read
  # the information from the store. However in this case we are not
  # actually using a storage file, we are using a "storage bypass" file,
  # and since some parts of the codebase expect this to be set (an
  # interface if you want to call it that way, although the storage
  # has not been abstracted into an interface, perhaps it should be)
  # then this has to be set. And the interface behavior is to return
  # a list of all available storage information objects (or all pre_obj
  # stored in the storage file)
  def GetStorageInformation(self):
    """Return information about the storage object (used by output modules)."""
    return [self._pre_obj]

  def WriteEventObjects(self):
    """Writes the event objects that are pushed on the queue."""
    output_class = output.GetOutputFormatter(self._output_module_string)
    if not output_class:
      output_class = output.GetOutputFormatter('Lst2csv')

    self._output_module = output_class(
        self, self._output_file, config=self._pre_obj)
    self._output_module.Start()
    self.ConsumeEventObjects()
    self._output_module.End()
