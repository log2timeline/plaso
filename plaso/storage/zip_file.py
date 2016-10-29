# -*- coding: utf-8 -*-
"""ZIP-based storage.

The ZIP-based storage can be described as a collection of storage files
(named streams) bundled in a single ZIP archive file.

There are multiple types of streams:
* error_data.#
  The error data streams contain the serialized error objects.
* error_index.#
  The error index streams contain the stream offset to the serialized
  error objects.
* event_data.#
  The event data streams contain the serialized events.
* event_index.#
  The event index streams contain the stream offset to the serialized
  events.
* event_source_data.#
  The event source data streams contain the serialized event source objects.
* event_source_index.#
  The event source index streams contain the stream offset to the serialized
  event source objects.
* event_tag_data.#
  The event tag data streams contain the serialized event tag objects.
* event_tag_index.#
  The event tag index streams contain the stream offset to the serialized
  event tag objects.
* event_timestamps.#
  The event timestamps streams contain the timestamp of the serialized
  events.
* metadata.txt
  Stream that contains the storage metadata.
* preprocess.#
  Stream that contains the preprocessing information.
  Only applies to session-based storage.
* session_completion.#
  Stream that contains information about the completion of a session.
  Only applies to session-based storage.
* session_start.#
  Stream that contains information about the start of a session.
  Only applies to session-based storage.
* task_completion.#
  Stream that contains information about the completion of a task.
  Only applies to task-based storage.
* task_start.#
  Stream that contains information about the start of a task.
  Only applies to task-based storage.

The # in a stream name is referred to as the "store number". Streams with
the same prefix e.g. "event_" and "store number" are related.

+ The event data streams

The event data streams contain the serialized events. The serialized
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
+-----+-----+-...-+
| int | int | ... |
+-----+-----+-...-+

+ The event timestamps stream

The event timestamps streams contain the timestamp of the serialized
events.

An event data stream consists of an array of 64-bit integers:
+-----------+-----------+-...-+
| timestamp | timestamp | ... |
+-----------+-----------+-...-+

+ The event tag index stream

The event tag index streams contain information about the event
the tag applies to.

An event data stream consists of an array of event tag index values.
+--------+--------+-...-+
| struct | struct | ... |
+--------+--------+-...-+

See the _SerializedEventTagIndexTable class for more information about
the actual structure of an event tag index value.

+ Version information

Deprecated in version 20160715:
* information.dump
  The serialized preprocess objects.

Deprecated in version 20160501:
* serializer.txt
  Stream that contains the serializer format.

Deprecated in version 20160511:
* plaso_index.#
  The event index streams contain the stream offset to the serialized
  events.
* plaso_proto.#
  The event data streams contain the serialized events.
* plaso_report.#
* plaso_tagging.#
  The event tag data streams contain the serialized event tag objects.
* plaso_tag_index.#
  The event tag index streams contain the stream offset to the serialized
  event tag objects.
* plaso_timestamps.#
  The event timestamps streams contain the timestamp of the serialized
  events.
"""

import heapq
import io
import logging
import os
import shutil
import tempfile
import time
import warnings
import zipfile

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error

import construct

from plaso.containers import sessions
from plaso.lib import definitions
from plaso.lib import platform_specific
from plaso.serializer import json_serializer
from plaso.storage import interface
from plaso.storage import gzip_file


class _AttributeContainersList(object):
  """Class that defines the attribute containers list.

  The list is unsorted and pops attribute containers in the same order as
  pushed to preserve order.

  The GetAttributeContainerByIndex method should be used to read attribute
  containers from the list while it being filled.

  Attributes:
    data_size (int): total data size of the serialized attribute containers
        on the list.
  """

  def __init__(self):
    """Initializes an attribute container list."""
    super(_AttributeContainersList, self).__init__()
    self._list = []
    self.data_size = 0

  @property
  def number_of_attribute_containers(self):
    """int: number of serialized attribute containers on the list."""
    return len(self._list)

  def Empty(self):
    """Empties the list."""
    self._list = []
    self.data_size = 0

  def GetAttributeContainerByIndex(self, index):
    """Retrieves a specific attribute container from the list.

    Args:
      index (int): attribute container index.

    Returns:
      bytes: serialized attribute container data.
    """
    if index < len(self._list):
      return self._list[index]

  def PopAttributeContainer(self):
    """Pops an attribute container from the list.

    Returns:
      bytes: serialized attribute container data.
    """
    try:
      serialized_data = self._list.pop(0)
      self.data_size -= len(serialized_data)
      return serialized_data

    except IndexError:
      return

  def PushAttributeContainer(self, serialized_data):
    """Pushes an attribute container onto the list.

    Args:
      serialized_data (bytes): serialized attribute container data.
    """
    self._list.append(serialized_data)
    self.data_size += len(serialized_data)


class _EventsHeap(object):
  """Class that defines the events heap."""

  def __init__(self):
    """Initializes an events heap."""
    super(_EventsHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  def PeekEvent(self):
    """Retrieves the first event from the heap without removing it.

    Returns:
      tuple: contains:

        EventObject: event or None.
        int: number of the stream or None.
    """
    try:
      _, stream_number, _, event = self._heap[0]
      return event, stream_number

    except IndexError:
      return None, None

  def PopEvent(self):
    """Retrieves and removes the first event from the heap.

    Returns:
      tuple: contains:

        EventObject: event or None.
        int: number of the stream or None.
    """
    try:
      _, stream_number, _, event = heapq.heappop(self._heap)
      return event, stream_number

    except IndexError:
      return None, None

  def PushEvent(self, event, stream_number, entry_index):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
      stream_number (int): serialized data stream number.
      entry_index (int): serialized data stream entry index.
    """
    heap_values = (event.timestamp, stream_number, entry_index, event)
    heapq.heappush(self._heap, heap_values)


class _SerializedEventsHeap(object):
  """Class that defines the serialized events heap.

  Attributes:
    data_size (int): total data size of the serialized events on the heap.
  """

  def __init__(self):
    """Initializes a serialized events heap."""
    super(_SerializedEventsHeap, self).__init__()
    self._heap = []
    self.data_size = 0

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  def Empty(self):
    """Empties the heap."""
    self._heap = []
    self.data_size = 0

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      A tuple containing an integer containing the event timestamp and
      a binary string containing the serialized event data.
      If the heap is empty the values in the tuple will be None.
    """
    try:
      timestamp, event_data = heapq.heappop(self._heap)

      self.data_size -= len(event_data)
      return timestamp, event_data

    except IndexError:
      return None, None

  def PushEvent(self, timestamp, event_data):
    """Pushes a serialized event onto the heap.

    Args:
      timestamp (int): event timestamp, which contains the number of
          micro seconds since January 1, 1970, 00:00:00 UTC.
      event_data (bytes): serialized event data.
    """
    heap_values = (timestamp, event_data)
    heapq.heappush(self._heap, heap_values)
    self.data_size += len(event_data)


class _EventTagIndexValue(object):
  """Class that defines the event tag index value.

  Attributes:
    event_uuid (str): event identifier formatted as an UUID.
    offset (int): serialized event tag data offset.
    store_number (int): serialized data stream number.
    store_index (int): serialized data stream entry index.
    tag_type (int): tag type.
  """
  TAG_TYPE_UNDEFINED = 0
  TAG_TYPE_NUMERIC = 1
  TAG_TYPE_UUID = 2

  def __init__(
      self, tag_type, offset, event_uuid=None, store_number=None,
      store_index=None):
    """Initializes the tag index value.

    Args:
      tag_type (int): tag type.
      offset (int): serialized event tag data offset.
      event_uuid (Optional[str]): event identifier formatted as an UUID.
      store_number (Optional[int]): serialized data stream number.
      store_index (Optional[int]): serialized data stream entry index.
    """
    super(_EventTagIndexValue, self).__init__()
    self._identifier = None
    self.event_uuid = event_uuid
    self.offset = offset
    self.store_number = store_number
    self.store_index = store_index
    self.tag_type = tag_type

  def __getitem__(self, key):
    """Retrieves a specific instance attribute.

    This function is needed to support construct._build() as used
    as of version 2.5.3.

    Args:
      key (str): attribute name.

    Returns:
      object: attribute value.

    Raises:
      KeyError: if the instance does not have the attribute.
    """
    if not hasattr(self, key):
      raise KeyError(u'No such attribute: {0:s}'.format(key))

    return getattr(self, key)

  def __str__(self):
    """str: string representation of the event tag identifier."""
    string = u'tag_type: {0:d} offset: 0x{1:08x}'.format(
        self.tag_type, self.offset)

    if self.tag_type == self.TAG_TYPE_NUMERIC:
      return u'{0:s} store_number: {1:d} store_index: {2:d}'.format(
          string, self.store_number, self.store_index)

    elif self.tag_type == self.TAG_TYPE_UUID:
      return u'{0:s} event_uuid: {1:s}'.format(string, self.event_uuid)

    return string

  @property
  def identifier(self):
    """str: event identifier."""
    if not self._identifier:
      if self.tag_type == self.TAG_TYPE_NUMERIC:
        self._identifier = u'{0:d}:{1:d}'.format(
            self.store_number, self.store_index)

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
    """Initializes a serialized data stream.

    Args:
      zip_file (zipfile.ZipFile): ZIP file that contains the stream.
      storage_file_path (str): path of the storage file.
      stream_name (str): name of the stream.
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
    """int: entry index."""
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
      bytes: data or None if no data remaining.

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
      entry_index (int): serialized data stream entry index.
      stream_offset (int): data stream offset.
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
      # Since zipfile.ZipExtFile is not seekable we need to read up to
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
      data (bytes): data.

    Returns:
      int: offset of the entry within the temporary file.

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
      int: offset of the entry within the temporary file.

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
      int: offset of the entry within the temporary file.

    Raises:
      IOError: if the serialized data stream cannot be written.
    """
    stream_file_path = os.path.join(self._path, self._stream_name)
    self._file_object = open(stream_file_path, 'wb')
    if platform_specific.PlatformIsWindows():
      file_handle = self._file_object.fileno()
      platform_specific.DisableWindowsFileHandleInheritance(file_handle)
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
    """Initializes a serialized data offset table.

    Args:
      zip_file (zipfile.ZipFile): ZIP file that contains the stream.
      stream_name (str): name of the stream.
    """
    super(_SerializedDataOffsetTable, self).__init__()
    self._offsets = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  @property
  def number_of_offsets(self):
    """int: number of offsets."""
    return len(self._offsets)

  def AddOffset(self, offset):
    """Adds an offset.

    Args:
      offset (int): offset.
    """
    self._offsets.append(offset)

  def GetOffset(self, entry_index):
    """Retrieves a specific serialized data offset.

    Args:
      entry_index (int): table entry index.

    Returns:
      int: serialized data offset.

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
    """Initializes a serialized data timestamp table.

    Args:
      zip_file (zipfile.ZipFile): ZIP file that contains the stream.
      stream_name (str): name of the stream.
    """
    super(_SerializedDataTimestampTable, self).__init__()
    self._stream_name = stream_name
    self._timestamps = []
    self._zip_file = zip_file

  @property
  def number_of_timestamps(self):
    """int: number of timestamps."""
    return len(self._timestamps)

  def AddTimestamp(self, timestamp):
    """Adds a timestamp.

    Args:
      timestamp (int): event timestamp, which contains the number of
          micro seconds since January 1, 1970, 00:00:00 UTC.
    """
    self._timestamps.append(timestamp)

  def GetTimestamp(self, entry_index):
    """Retrieves a specific timestamp.

    Args:
      entry_index (int): table entry index.

    Returns:
      int: event timestamp, which contains the number of micro seconds since
          January 1, 1970, 00:00:00 UTC.

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
      construct.ULInt32(u'store_index'))

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
    """Initializes a serialized event tag index table.

    Args:
      zip_file (zipfile.ZipFile): ZIP file that contains the stream.
      stream_name (str): name of the stream.
    """
    super(_SerializedEventTagIndexTable, self).__init__()
    self._event_tag_indexes = []
    self._stream_name = stream_name
    self._zip_file = zip_file

  @property
  def number_of_entries(self):
    """int: number of event tag index entries."""
    return len(self._event_tag_indexes)

  def AddEventTagIndex(
      self, tag_type, offset, event_uuid=None, store_number=None,
      store_index=None):
    """Adds an event tag index.

    Args:
      tag_type (int): event tag type.
      offset (int): serialized event tag data offset.
      event_uuid (Optional[str]): event identifier formatted as an UUID.
      store_number (Optional[str]): store number.
      store_index (Optional[str]): index relative to the start of the store.
    """
    event_tag_index = _EventTagIndexValue(
        tag_type, offset, event_uuid=event_uuid, store_number=store_number,
        store_index=store_index)
    self._event_tag_indexes.append(event_tag_index)

  def GetEventTagIndex(self, entry_index):
    """Retrieves a specific event tag index.

    Args:
      entry_index (int): table entry index.

    Returns:
      _EventTagIndexValue: event tag index value.

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
        tag_index = tag_index_struct.get(u'tag', {})
        event_uuid = tag_index.get(u'event_uuid', None)
        store_number = tag_index.get(u'store_number', stream_store_number)
        store_index = tag_index.get(u'store_index', None)

        event_tag_index = _EventTagIndexValue(
            tag_type, offset, event_uuid=event_uuid, store_number=store_number,
            store_index=store_index)
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
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  def __init__(self):
    """Initializes storage metadata."""
    super(_StorageMetadata, self).__init__()
    self.format_version = None
    self.serialization_format = None
    self.storage_type = None


class _StorageMetadataReader(object):
  """Class that implements a storage metadata reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name).decode('utf-8')
    except (configparser.NoOptionError, configparser.NoSectionError):
      return

  def Read(self, stream_data):
    """Reads the storage metadata.

    Args:
      stream_data (bytes): data of the steam.

    Returns:
      _StorageMetadata: storage metadata.
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

    storage_metadata.storage_type = self._GetConfigValue(
        config_parser, section_name, u'storage_type')

    if not storage_metadata.storage_type:
      storage_metadata.storage_type = definitions.STORAGE_TYPE_SESSION

    return storage_metadata


class ZIPStorageFile(interface.BaseFileStorage):
  """Class that defines the ZIP-based storage file.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  # The format version.
  _FORMAT_VERSION = 20160715

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _COMPATIBLE_FORMAT_VERSION = 20160715

  # The maximum buffer size of serialized data before triggering
  # a flush to disk (64 MiB).
  _MAXIMUM_BUFFER_SIZE = 64 * 1024 * 1024

  # The maximum number of cached tables.
  _MAXIMUM_NUMBER_OF_CACHED_TABLES = 5

  # The maximum serialized report size (32 MiB).
  _MAXIMUM_SERIALIZED_REPORT_SIZE = 32 * 1024 * 1024

  _MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS = 5
  _LOCKED_FILE_SLEEP_TIME = 0.5

  def __init__(
      self, maximum_buffer_size=0,
      storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a ZIP-based storage file.

    Args:
      maximum_buffer_size (Optional[int]):
          maximum size of a single storage stream. A value of 0 indicates
          the limit is _MAXIMUM_BUFFER_SIZE.
      storage_type (Optional[str]): storage type.

    Raises:
      ValueError: if the maximum buffer size value is out of bounds.
    """
    if (maximum_buffer_size < 0 or
        maximum_buffer_size > self._MAXIMUM_BUFFER_SIZE):
      raise ValueError(u'Maximum buffer size value out of bounds.')

    if not maximum_buffer_size:
      maximum_buffer_size = self._MAXIMUM_BUFFER_SIZE

    super(ZIPStorageFile, self).__init__()
    self._analysis_report_stream_number = 0
    self._error_stream_number = 1
    self._errors_list = _AttributeContainersList()
    self._event_offset_tables = {}
    self._event_offset_tables_lfu = []
    self._event_stream_number = 1
    self._event_streams = {}
    self._event_source_offset_tables = {}
    self._event_source_offset_tables_lfu = []
    self._event_source_stream_number = 1
    self._event_source_streams = {}
    self._event_sources_in_stream = []
    self._event_sources_list = _AttributeContainersList()
    self._event_tag_index = None
    self._event_tag_stream_number = 1
    self._event_timestamp_tables = {}
    self._event_timestamp_tables_lfu = []
    self._event_heap = None
    self._last_preprocess = 0
    self._last_session = 0
    self._last_task = 0
    self._maximum_buffer_size = maximum_buffer_size
    self._serialized_event_tags = []
    self._serialized_event_tags_size = 0
    self._serialized_events_heap = _SerializedEventsHeap()
    self._path = None
    self._zipfile = None
    self._zipfile_path = None

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

  def _BuildTagIndex(self):
    """Builds the tag index that contains the offsets for each tag.

    Raises:
      IOError: if the stream cannot be opened.
    """
    self._event_tag_index = {}

    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(u'event_tag_index.'):
        continue

      event_tag_index_table = _SerializedEventTagIndexTable(
          self._zipfile, stream_name)
      event_tag_index_table.Read()

      for entry_index in range(event_tag_index_table.number_of_entries):
        tag_index_value = event_tag_index_table.GetEventTagIndex(entry_index)
        self._event_tag_index[tag_index_value.identifier] = tag_index_value

  def _FillEventHeapFromStream(self, stream_number):
    """Fills the event heap with the next events from the stream.

    This function will read events starting at the current stream entry that
    have the same timestamp and adds them to the heap. This ensures that the
    sorting order of events with the same timestamp is consistent.

    Except for the last event, all newly added events will have the same
    timestamp.

    Args:
      stream_number (int): serialized data stream number.
    """
    event = self._GetEvent(stream_number)
    if not event:
      return

    self._event_heap.PushEvent(event, stream_number, event.store_index)

    reference_timestamp = event.timestamp
    while event.timestamp == reference_timestamp:
      event = self._GetEvent(stream_number)
      if not event:
        break

      self._event_heap.PushEvent(event, stream_number, event.store_index)

  def _GetEvent(self, stream_number, entry_index=-1):
    """Reads an event from a specific stream.

    Args:
      stream_number (int): number of the serialized event object stream.
      entry_index (Optional[int]): number of the serialized event within
          the stream, where -1 represents the next available event.

    Returns:
      EventObject: event or None.
    """
    event_data, entry_index = self._GetEventSerializedData(
        stream_number, entry_index=entry_index)
    if not event_data:
      return

    event = self._DeserializeAttributeContainer(event_data, u'event')

    event.store_number = stream_number
    event.store_index = entry_index

    return event

  def _GetEventSerializedData(self, stream_number, entry_index=-1):
    """Retrieves specific event serialized data.

    By default the first available entry in the specific serialized stream
    is read, however any entry can be read using the index stream.

    Args:
      stream_number (int): number of the serialized event object stream.
      entry_index (Optional[int]): number of the serialized event within
          the stream, where -1 represents the next available event.

    Returns:
      A tuple containing the event serialized data and the entry index
      of the event within the storage file.

    Raises:
      IOError: if the stream cannot be opened.
      ValueError: if the entry index is out of bounds.
    """
    if entry_index < -1:
      raise ValueError(u'Entry index out of bounds.')

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
      except (IndexError, IOError):
        logging.error((
            u'Unable to read entry index: {0:d} from serialized data stream: '
            u'{1:d}').format(entry_index, stream_number))
        return None, None

      data_stream.SeekEntryAtOffset(entry_index, stream_offset)

    event_entry_index = data_stream.entry_index
    try:
      event_data = data_stream.ReadEntry()
    except IOError as exception:
      logging.error((
          u'Unable to read entry from serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    return event_data, event_entry_index

  def _GetEventSource(self, stream_number, entry_index=-1):
    """Reads an event source from a specific stream.

    Args:
      stream_number (int): number of the serialized event source object stream.
      entry_index (Optional[int]): number of the serialized event source
          within the stream, where -1 represents the next available event
          source.

    Returns:
      EventSource: event source or None.
    """
    event_source_data, entry_index = self._GetEventSourceSerializedData(
        stream_number, entry_index=entry_index)
    if not event_source_data:
      return

    return self._DeserializeAttributeContainer(
        event_source_data, u'event_source')

  def _GetEventSourceSerializedData(self, stream_number, entry_index=-1):
    """Retrieves specific event source serialized data.

    By default the first available entry in the specific serialized stream
    is read, however any entry can be read using the index stream.

    Args:
      stream_number (int): number of the serialized event source object stream.
      entry_index (Optional[int]): number of the serialized event source
          within the stream, where -1 represents the next available event
          source.

    Returns:
      A tuple containing the event source serialized data and the entry index
      of the event source within the storage file.

    Raises:
      IOError: if the stream cannot be opened.
      ValueError: if the entry index is out of bounds.
    """
    if entry_index < -1:
      raise ValueError(u'Entry index out of bounds.')

    try:
      data_stream = self._GetSerializedEventSourceStream(stream_number)
    except IOError as exception:
      logging.error((
          u'Unable to retrieve serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    if entry_index >= 0:
      try:
        offset_table = self._GetSerializedEventSourceOffsetTable(stream_number)
        stream_offset = offset_table.GetOffset(entry_index)
      except (IOError, IndexError):
        logging.error((
            u'Unable to read entry index: {0:d} from serialized data stream: '
            u'{1:d}').format(entry_index, stream_number))
        return None, None

      data_stream.SeekEntryAtOffset(entry_index, stream_offset)

    event_source_entry_index = data_stream.entry_index
    try:
      event_source_data = data_stream.ReadEntry()
    except IOError as exception:
      logging.error((
          u'Unable to read entry from serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    return event_source_data, event_source_entry_index

  def _GetEventTagIndexValue(self, store_number, entry_index, uuid):
    """Retrieves an event tag index value.

    Args:
      store_number (int): store number.
      entry_index (int): serialized data stream entry index.
      uuid (str): event identifier formatted as an UUID.

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

  def _GetLastStreamNumber(self, stream_name_prefix):
    """Retrieves the last stream number.

    Args:
      stream_name_prefix (str): stream name prefix.

    Returns:
      int: last stream number.

    Raises:
      IOError: if the stream number format is not supported.
    """
    last_stream_number = 0
    for stream_name in self._GetStreamNames():
      if stream_name.startswith(stream_name_prefix):
        _, _, stream_number = stream_name.partition(u'.')

        try:
          stream_number = int(stream_number, 10)
        except ValueError:
          raise IOError(
              u'Unsupported stream number: {0:s}'.format(stream_number))

        if stream_number > last_stream_number:
          last_stream_number = stream_number

    return last_stream_number + 1

  def _GetSerializedDataStream(
      self, streams_cache, stream_name_prefix, stream_number):
    """Retrieves the serialized data stream.

    Args:
      streams_cache (dict): streams cache.
      stream_name_prefix (str): stream name prefix.
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataStream: serialized data stream.

    Raises:
      IOError: if the stream cannot be opened.
    """
    data_stream = streams_cache.get(stream_number, None)
    if not data_stream:
      stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)
      streams_cache[stream_number] = data_stream

    return data_stream

  def _GetSerializedDataOffsetTable(
      self, offset_tables_cache, offset_tables_lfu, stream_name_prefix,
      stream_number):
    """Retrieves the serialized data offset table.

    Args:
      offset_tables_cache (dict): offset tables cache.
      offset_tables_lfu (list[_SerializedDataOffsetTable]): least frequently
          used (LFU) offset tables.
      stream_name_prefix (str): stream name prefix.
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataOffsetTable: serialized data offset table.

    Raises:
      IOError: if the stream cannot be opened.
    """
    offset_table = offset_tables_cache.get(stream_number, None)
    if not offset_table:
      stream_name = u'{0:s}.{1:06d}'.format(stream_name_prefix, stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)
      offset_table.Read()

      number_of_tables = len(offset_tables_cache)
      if number_of_tables >= self._MAXIMUM_NUMBER_OF_CACHED_TABLES:
        lfu_stream_number = offset_tables_lfu.pop()
        del offset_tables_cache[lfu_stream_number]

      offset_tables_cache[stream_number] = offset_table

    if stream_number in offset_tables_lfu:
      lfu_index = offset_tables_lfu.index(stream_number)
      offset_tables_lfu.pop(lfu_index)

    offset_tables_lfu.append(stream_number)

    return offset_table

  def _GetSerializedDataStreamNumbers(self, stream_name_prefix):
    """Retrieves the available serialized data stream numbers.

    Args:
      stream_name_prefix (str): stream name prefix.

    Returns:
      list[int]: available serialized data stream numbers sorted numerically.
    """
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

  def _GetSerializedEventOffsetTable(self, stream_number):
    """Retrieves the serialized event stream offset table.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataOffsetTable: serialized data offset table.

    Raises:
      IOError: if the stream cannot be opened.
    """
    return self._GetSerializedDataOffsetTable(
        self._event_offset_tables, self._event_offset_tables_lfu,
        u'event_index', stream_number)

  def _GetSerializedEventSourceOffsetTable(self, stream_number):
    """Retrieves the serialized event source stream offset table.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataOffsetTable: serialized data offset table.

    Raises:
      IOError: if the stream cannot be opened.
    """
    return self._GetSerializedDataOffsetTable(
        self._event_source_offset_tables, self._event_source_offset_tables_lfu,
        u'event_source_index', stream_number)

  def _GetSerializedEventSourceStream(self, stream_number):
    """Retrieves the serialized event source stream.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataStream: serialized data stream.

    Raises:
      IOError: if the stream cannot be opened.
    """
    return self._GetSerializedDataStream(
        self._event_source_streams, u'event_source_data', stream_number)

  def _GetSerializedEventStream(self, stream_number):
    """Retrieves the serialized event stream.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataStream: serialized data stream.

    Raises:
      IOError: if the stream cannot be opened.
    """
    return self._GetSerializedDataStream(
        self._event_streams, u'event_data', stream_number)

  def _GetSerializedEventSourceStreamNumbers(self):
    """Retrieves the available serialized event source stream numbers.

    Returns:
      list[int]: available serialized data stream numbers sorted numerically.
    """
    return self._GetSerializedDataStreamNumbers(u'event_source_data.')

  def _GetSerializedEventStreamNumbers(self):
    """Retrieves the available serialized event stream numbers.

    Returns:
      list[int]: available serialized data stream numbers sorted numerically.
    """
    return self._GetSerializedDataStreamNumbers(u'event_data.')

  def _GetSerializedEventTimestampTable(self, stream_number):
    """Retrieves the serialized event stream timestamp table.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataTimestampTable: serialized data timestamp table.

    Raises:
      IOError: if the stream cannot be opened.
    """
    timestamp_table = self._event_timestamp_tables.get(stream_number, None)
    if not timestamp_table:
      stream_name = u'event_timestamps.{0:06d}'.format(stream_number)
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

  def _GetStreamNames(self):
    """Retrieves the stream names.

    Yields:
      str: stream name.
    """
    if self._zipfile:
      for stream_name in self._zipfile.namelist():
        yield stream_name

  def _GetSortedEvent(self, time_range=None):
    """Retrieves the next event in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      EventObject: event.
    """
    if not self._event_heap:
      self._InitializeMergeBuffer(time_range=time_range)
      if not self._event_heap:
        return

    event, stream_number = self._event_heap.PopEvent()
    if not event:
      return

    # Stop as soon as we hit the upper bound.
    if time_range and event.timestamp > time_range.end_timestamp:
      return

    # Peek at the next event and determine if we need fill the heap
    # with the next events from the stream.
    next_event, next_stream_number = self._event_heap.PeekEvent()
    if (not next_event or next_stream_number != stream_number or
        next_event.timestamp != event.timestamp):
      self._FillEventHeapFromStream(stream_number)

    event.tag = self._ReadEventTagByIdentifier(
        event.store_number, event.store_index, event.uuid)

    return event

  def _HasStream(self, stream_name):
    """Determines if the ZIP file contains a specific stream.

    Args:
      stream_name (str): name of the stream.

    Returns:
      bool: True if the ZIP file contains the stream.
    """
    try:
      file_object = self._zipfile.open(stream_name, 'r')
    except KeyError:
      return False

    file_object.close()
    return True

  def _InitializeMergeBuffer(self, time_range=None):
    """Initializes the events into the merge buffer.

    This function fills the merge buffer with the first relevant event
    from each stream.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.
    """
    self._event_heap = _EventsHeap()

    number_range = self._GetSerializedEventStreamNumbers()
    for stream_number in number_range:
      entry_index = -1
      if time_range:
        stream_name = u'event_timestamps.{0:06d}'.format(stream_number)
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

      event = self._GetEvent(stream_number, entry_index=entry_index)
      # Check the lower bound in case no timestamp table was available.
      while (event and time_range and
             event.timestamp < time_range.start_timestamp):
        event = self._GetEvent(stream_number)

      if event:
        if time_range and event.timestamp > time_range.end_timestamp:
          continue

        self._event_heap.PushEvent(
            event, stream_number, event.store_number)

        reference_timestamp = event.timestamp
        while event.timestamp == reference_timestamp:
          event = self._GetEvent(stream_number)
          if not event:
            break

          self._event_heap.PushEvent(
              event, stream_number, event.store_number)

  def _OpenRead(self):
    """Opens the storage file for reading."""
    has_storage_metadata = self._ReadStorageMetadata()
    if not has_storage_metadata:
      # TODO: remove serializer.txt stream support in favor
      # of storage metatdata.
      if self._read_only:
        logging.warning(u'Storage file does not contain a metadata stream.')

      stored_serialization_format = self._ReadSerializerStream()
      if stored_serialization_format:
        self.serialization_format = stored_serialization_format

    if self.serialization_format != definitions.SERIALIZER_FORMAT_JSON:
      raise IOError(u'Unsupported serialization format: {0:s}'.format(
          self.serialization_format))

    self._serializer = json_serializer.JSONAttributeContainerSerializer

    self._error_stream_number = self._GetLastStreamNumber(u'error_data.')
    self._event_stream_number = self._GetLastStreamNumber(u'event_data.')
    self._event_source_stream_number = self._GetLastStreamNumber(
        u'event_source_data.')
    self._event_tag_stream_number = self._GetLastStreamNumber(
        u'event_tag_data.')

    self._analysis_report_stream_number = self._GetLastStreamNumber(
        u'analysis_report_data.')
    self._last_preprocess = self._GetLastStreamNumber(u'preprocess.')

    last_session_start = self._GetLastStreamNumber(u'session_start.')
    last_session_completion = self._GetLastStreamNumber(u'session_completion.')

    # TODO: handle open sessions.
    if last_session_start != last_session_completion:
      logging.warning(u'Detected unclosed session.')

    self._last_session = last_session_completion

    last_task_start = self._GetLastStreamNumber(u'task_start.')
    last_task_completion = self._GetLastStreamNumber(u'task_completion.')

    # TODO: handle open tasks.
    if last_task_start != last_task_completion:
      logging.warning(u'Detected unclosed task.')

    self._last_task = last_task_completion

  def _OpenStream(self, stream_name, access_mode='r'):
    """Opens a stream.

    Args:
      stream_name (str): name of the stream.
      access_mode (Optional[str]): access mode.

    Returns:
      zipfile.ZipExtFile: stream file-like object or None.
    """
    try:
      return self._zipfile.open(stream_name, mode=access_mode)
    except KeyError:
      return

  def _OpenWrite(self):
    """Opens the storage file for writing."""
    if self._event_stream_number == 1:
      self._WriteStorageMetadata()

  def _OpenZIPFile(self, path, read_only):
    """Opens the ZIP file.

    Args:
      path (str): path of the ZIP file.
      read_only (bool): True if the file should be opened in read-only mode.

    Raises:
      IOError: if the ZIP file is already opened or if the ZIP file cannot
               be opened.
    """
    if self._zipfile:
      raise IOError(u'ZIP file already opened.')

    if read_only:
      access_mode = 'r'

      zipfile_path = path
    else:
      access_mode = 'a'

      # Create a temporary directory to prevent multiple ZIP storage
      # files in the same directory conflicting with each other.
      directory_name = os.path.dirname(path)
      basename = os.path.basename(path)
      directory_name = tempfile.mkdtemp(dir=directory_name)
      zipfile_path = os.path.join(directory_name, basename)

      if os.path.exists(path):
        for attempt in range(1, self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS):
          try:
            os.rename(path, zipfile_path)
            break

          except OSError:
            if attempt == self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS:
              raise
            time.sleep(self._LOCKED_FILE_SLEEP_TIME)

    try:
      self._zipfile = zipfile.ZipFile(
          zipfile_path, mode=access_mode, compression=zipfile.ZIP_DEFLATED,
          allowZip64=True)
      self._zipfile_path = zipfile_path
      if platform_specific.PlatformIsWindows():
        file_handle = self._zipfile.fp.fileno()
        platform_specific.DisableWindowsFileHandleInheritance(file_handle)

    except zipfile.BadZipfile as exception:
      raise IOError(u'Unable to open ZIP file: {0:s} with error: {1:s}'.format(
          zipfile_path, exception))

    self._is_open = True
    self._path = path
    self._read_only = read_only

  def _ReadAttributeContainerFromStreamEntry(self, data_stream, container_type):
    """Reads an attribute container entry from a data stream.

    Args:
      data_stream (_SerializedDataStream): data stream.
      container_type (str): attribute container type.

    Returns:
      AttributeContainer: attribute container or None.
    """
    entry_data = data_stream.ReadEntry()
    return self._DeserializeAttributeContainer(entry_data, container_type)

  def _ReadAttributeContainersFromStream(self, data_stream, container_type):
    """Reads attribute containers from a data stream.

    Args:
      data_stream (_SerializedDataStream): data stream.
      container_type (str): attribute container type.

    Yields:
      AttributeContainer: attribute container.
    """
    attribute_container = self._ReadAttributeContainerFromStreamEntry(
        data_stream, container_type)

    while attribute_container:
      yield attribute_container

      attribute_container = self._ReadAttributeContainerFromStreamEntry(
          data_stream, container_type)

  def _ReadEventTagByIdentifier(self, store_number, entry_index, uuid):
    """Reads an event tag by identifier.

    Args:
      store_number (int): store number.
      entry_index (int): serialized data stream entry index.
      uuid (str): event identifier formatted as an UUID.

    Returns:
      EventTag: event tag or None.

    Raises:
      IOError: if the event tag data stream cannot be opened.
    """
    tag_index_value = self._GetEventTagIndexValue(
        store_number, entry_index, uuid)
    if tag_index_value is None:
      return

    stream_name = u'event_tag_data.{0:06d}'.format(tag_index_value.store_number)
    if not self._HasStream(stream_name):
      raise IOError(u'No such stream: {0:s}'.format(stream_name))

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.SeekEntryAtOffset(entry_index, tag_index_value.offset)

    return self._ReadAttributeContainerFromStreamEntry(data_stream, u'event')

  def _ReadSerializerStream(self):
    """Reads the serializer stream.

    Note that the serializer stream has been deprecated in format version
    20160501 in favor of the the store metadata stream.

    Returns:
      str: stored serializer format.

    Raises:
      ValueError: if the serializer format is not supported.
    """
    stream_name = u'serializer.txt'
    if not self._HasStream(stream_name):
      return

    serialization_format = self._ReadStream(stream_name)
    if serialization_format != definitions.SERIALIZER_FORMAT_JSON:
      raise ValueError(
          u'Unsupported stored serialization format: {0:s}'.format(
              serialization_format))

    return serialization_format

  def _ReadStorageMetadata(self):
    """Reads the storage metadata.

    Returns:
      bool: True if the storage metadata was read.

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
      raise IOError(u'Unsupported serialization format: {0:s}'.format(
          serialization_format))

    if storage_metadata.storage_type not in definitions.STORAGE_TYPES:
      raise IOError(u'Unsupported storage type: {0:s}'.format(
          storage_metadata.storage_type))

    self.format_version = storage_metadata.format_version
    self.serialization_format = serialization_format
    self.storage_type = storage_metadata.storage_type

    return True

  def _ReadStream(self, stream_name):
    """Reads data from a stream.

    Args:
      stream_name (str): name of the stream.

    Returns:
      bytes: data of the stream.
    """
    file_object = self._OpenStream(stream_name)
    if not file_object:
      return b''

    try:
      data = file_object.read()
    finally:
      file_object.close()

    return data

  def _WriteAttributeContainersList(
      self, attribute_containers_list, stream_name_prefix, stream_number):
    """Writes the contents of an attribute containers list.

    Args:
      attribute_containers_list(_AttributeContainersList): attribute
          containers list.
      stream_name_prefix(str): stream name prefix.
      stream_number(int): stream number.
    """
    stream_name = u'{0:s}_index.{1:06d}'.format(
        stream_name_prefix, stream_number)
    offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)

    stream_name = u'{0:s}_data.{1:06d}'.format(
        stream_name_prefix, stream_number)
    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    entry_data_offset = data_stream.WriteInitialize()

    try:
      for _ in range(attribute_containers_list.number_of_attribute_containers):
        entry_data = attribute_containers_list.PopAttributeContainer()

        offset_table.AddOffset(entry_data_offset)

        entry_data_offset = data_stream.WriteEntry(entry_data)

    except:
      data_stream.WriteAbort()

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'write')

      raise

    offset_table.Write()
    data_stream.WriteFinalize()

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'write')

  def _WriteSerializedErrors(self):
    """Writes the buffered serialized errors."""
    if not self._errors_list.data_size:
      return

    self._WriteAttributeContainersList(
        self._errors_list, u'error',
        self._error_stream_number)

    self._error_stream_number += 1
    self._errors_list.Empty()

  def _WriteSerializedEvents(self):
    """Writes the serialized events."""
    if not self._serialized_events_heap.data_size:
      return

    self._WriteSerializedEventsHeap(
        self._serialized_events_heap, self._event_stream_number)

    self._event_stream_number += 1
    self._serialized_events_heap.Empty()

  def _WriteSerializedEventsHeap(self, serialized_events_heap, stream_number):
    """Writes the contents of an serialized events heap.

    Args:
      serialized_events_heap(_SerializedEventsHeap): serialized events heap.
      stream_number(int): stream number.
    """
    stream_name = u'event_index.{0:06d}'.format(stream_number)
    offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)

    stream_name = u'event_timestamps.{0:06d}'.format(stream_number)
    timestamp_table = _SerializedDataTimestampTable(self._zipfile, stream_name)

    stream_name = u'event_data.{0:06d}'.format(stream_number)
    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    entry_data_offset = data_stream.WriteInitialize()

    try:
      for _ in range(serialized_events_heap.number_of_events):
        timestamp, entry_data = serialized_events_heap.PopEvent()

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

  def _WriteSerializedEventSources(self):
    """Writes the serialized event sources."""
    if not self._event_sources_list.data_size:
      return

    self._WriteAttributeContainersList(
        self._event_sources_list, u'event_source',
        self._event_source_stream_number)

    self._event_source_stream_number += 1
    self._event_sources_list.Empty()

  def _WriteSerializedEventTags(self):
    """Writes the serialized event tags."""
    if not self._serialized_event_tags_size:
      return

    stream_name = u'event_tag_index.{0:06d}'.format(
        self._event_tag_stream_number)
    event_tag_index_table = _SerializedEventTagIndexTable(
        self._zipfile, stream_name)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    stream_name = u'event_tag_data.{0:06d}'.format(
        self._event_tag_stream_number)
    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    entry_data_offset = data_stream.WriteInitialize()

    try:
      for _ in range(len(self._serialized_event_tags)):
        heap_values = heapq.heappop(self._serialized_event_tags)
        store_number, store_index, event_uuid, entry_data = heap_values

        if event_uuid:
          tag_type = _EventTagIndexValue.TAG_TYPE_UUID
        else:
          tag_type = _EventTagIndexValue.TAG_TYPE_NUMERIC

        event_tag_index_table.AddEventTagIndex(
            tag_type, entry_data_offset, event_uuid=event_uuid,
            store_number=store_number, store_index=store_index)

        entry_data_offset = data_stream.WriteEntry(entry_data)

    except:
      data_stream.WriteAbort()

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'write')

      raise

    event_tag_index_table.Write()
    data_stream.WriteFinalize()

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'write')

    self._event_tag_stream_number += 1
    self._serialized_event_tags_size = 0
    self._serialized_event_tags = []

  def _WriteSessionCompletion(self, session_completion):
    """Writes a session completion attribute container.

    Args:
      session_completion (SessionCompletion): session completion attribute
          container.

    Raises:
      IOError: if the storage type does not support writing a session
               completion or the session completion already exists.
    """
    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Session completion not supported by storage type.')

    stream_name = u'session_completion.{0:06d}'.format(self._last_session)
    if self._HasStream(stream_name):
      raise IOError(u'Session completion: {0:06d} already exists.'.format(
          self._last_session))

    session_completion_data = self._SerializeAttributeContainer(
        session_completion)

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.WriteInitialize()
    data_stream.WriteEntry(session_completion_data)
    data_stream.WriteFinalize()

  def _WriteSessionStart(self, session_start):
    """Writes a session start attribute container

    Args:
      session_start (SessionStart): session start attribute container.

    Raises:
      IOError: if the storage type does not support writing a session
               start or the session start already exists.
    """
    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Session completion not supported by storage type.')

    stream_name = u'session_start.{0:06d}'.format(self._last_session)
    if self._HasStream(stream_name):
      raise IOError(u'Session start: {0:06d} already exists.'.format(
          self._last_session))

    session_start_data = self._SerializeAttributeContainer(session_start)

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.WriteInitialize()
    data_stream.WriteEntry(session_start_data)
    data_stream.WriteFinalize()

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    stream_name = u'metadata.txt'
    if self._HasStream(stream_name):
      return

    stream_data = (
        b'[plaso_storage_file]\n'
        b'format_version: {0:d}\n'
        b'serialization_format: {1:s}\n'
        b'storage_type: {2:s}\n'
        b'\n').format(
            self._FORMAT_VERSION, self.serialization_format, self.storage_type)

    self._WriteStream(stream_name, stream_data)

  def _WriteStream(self, stream_name, stream_data):
    """Writes data to a stream.

    Args:
      stream_name (str): name of the stream.
      stream_data (bytes): data of the steam.
    """
    # TODO: this can raise an IOError e.g. "Stale NFS file handle".
    # Determine if this be handled more error resiliently.

    # Prevent zipfile from generating "UserWarning: Duplicate name:".
    with warnings.catch_warnings():
      warnings.simplefilter(u'ignore')
      self._zipfile.writestr(stream_name, stream_data)

  def _WriteTaskCompletion(self, task_completion):
    """Writes a task completion attribute container.

    Args:
      task_completion (TaskCompletion): task completion attribute container.

    Raises:
      IOError: if the storage type does not support writing a task
               completion or the task completion already exists.
    """
    if self.storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task completion not supported by storage type.')

    stream_name = u'task_completion.{0:06d}'.format(self._last_task)
    if self._HasStream(stream_name):
      raise IOError(u'Task completion: {0:06d} already exists.'.format(
          self._last_task))

    task_completion_data = self._SerializeAttributeContainer(task_completion)

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.WriteInitialize()
    data_stream.WriteEntry(task_completion_data)
    data_stream.WriteFinalize()

  def _WriteTaskStart(self, task_start):
    """Writes a task start attribute container.

    Args:
      task_start (TaskStart): task start attribute container.

    Raises:
      IOError: if the storage type does not support writing a task start
               or the task start already exists.
    """
    if self.storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task start not supported by storage type.')

    stream_name = u'task_start.{0:06d}'.format(self._last_task)
    if self._HasStream(stream_name):
      raise IOError(u'Task start: {0:06d} already exists.'.format(
          self._last_task))

    task_start_data = self._SerializeAttributeContainer(task_start)

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.WriteInitialize()
    data_stream.WriteEntry(task_start_data)
    data_stream.WriteFinalize()

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    stream_name = u'analysis_report_data.{0:06}'.format(
        self._analysis_report_stream_number)

    serialized_report = self._SerializeAttributeContainer(analysis_report)

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.WriteInitialize()
    data_stream.WriteEntry(serialized_report)
    data_stream.WriteFinalize()

    self._analysis_report_stream_number += 1

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.

    Raises:
      IOError: when the storage file is closed or read-only or
               if the error cannot be serialized.
    """
    error.storage_session = self._last_session

    # We try to serialize the error first, so we can skip some
    # processing if it is invalid.
    error_data = self._SerializeAttributeContainer(error)

    self._errors_list.PushAttributeContainer(error_data)

    if self._errors_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedErrors()

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage file is closed or read-only or
               if the event cannot be serialized.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    # We try to serialize the event first, so we can skip some
    # processing if it is invalid.
    event_data = self._SerializeAttributeContainer(event)

    self._serialized_events_heap.PushEvent(event.timestamp, event_data)

    if self._serialized_events_heap.data_size > self._maximum_buffer_size:
      self._WriteSerializedEvents()

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

    Raises:
      IOError: when the storage file is closed or read-only or
               if the event source cannot be serialized.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    event_source.storage_session = self._last_session

    # We try to serialize the event source first, so we can skip some
    # processing if it is invalid.
    event_source_data = self._SerializeAttributeContainer(event_source)

    self._event_sources_list.PushAttributeContainer(event_source_data)

    if self._event_sources_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedEventSources()

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage file is closed or read-only or
               if the event tag cannot be serialized.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    # We try to serialize the event tag first, so we can skip some
    # processing if it is invalid.
    event_tag_data = self._SerializeAttributeContainer(event_tag)

    event_uuid = getattr(event_tag, u'event_uuid', None)
    store_index = getattr(event_tag, u'store_index', None)
    store_number = getattr(event_tag, u'store_number', None)

    heap_values = (store_number, store_index, event_uuid, event_tag_data)
    heapq.heappush(self._serialized_event_tags, heap_values)
    self._serialized_event_tags_size += len(event_tag_data)

    if self._serialized_event_tags_size > self._maximum_buffer_size:
      self._WriteSerializedEventSources()

  def AddEventTags(self, event_tags):
    """Adds event tags.

    Args:
      event_tags (list[EventTag]): event tags.

    Raises:
      IOError: when the storage file is closed or read-only or
               if the stream cannot be opened.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    if self._event_tag_index is None:
      self._BuildTagIndex()

    for event_tag in event_tags:
      tag_index_value = self._event_tag_index.get(event_tag.string_key, None)

      # This particular event has already been tagged on a previous occasion,
      # we need to make sure we are appending to that particular event tag.
      if tag_index_value is not None:
        stream_name = u'event_tag_data.{0:06d}'.format(
            tag_index_value.store_number)

        if not self._HasStream(stream_name):
          raise IOError(u'No such stream: {0:s}'.format(stream_name))

        data_stream = _SerializedDataStream(
            self._zipfile, self._zipfile_path, stream_name)
        # TODO: replace 0 by the actual event tag entry index.
        # This is for code consistency rather then a functional purpose.
        data_stream.SeekEntryAtOffset(0, tag_index_value.offset)

        # TODO: if stored_event_tag is cached make sure to update cache
        # after write.
        stored_event_tag = self._ReadAttributeContainerFromStreamEntry(
            data_stream, u'event_tag')
        if not stored_event_tag:
          continue

        event_tag.AddComment(stored_event_tag.comment)
        event_tag.AddLabels(stored_event_tag.labels)

      self.AddEventTag(event_tag)

    self._WriteSerializedEventTags()

    # TODO: Update the tags that have changed in the index instead
    # of flushing the index.

    # If we already built a list of tag in memory we need to clear that
    # since the tags have changed.
    if self._event_tag_index is not None:
      self._event_tag_index = None

  def Close(self):
    """Closes the storage file.

    Buffered attribute containers are written to file.

    Raises:
      IOError: if the storage file is already closed,
               if the event source cannot be serialized or
               if the storage file cannot be closed.
    """
    if not self._is_open:
      raise IOError(u'Storage file already closed.')

    if not self._read_only:
      self.Flush()

    if self._serializers_profiler:
      self._serializers_profiler.Write()

    # Make sure to flush the caches so that zipfile can be closed and freed.
    # Otherwise on Windows the ZIP file remains locked and cannot be renamed.

    self._event_offset_tables = {}
    self._event_offset_tables_lfu = []
    self._event_streams = {}

    self._event_source_offset_tables = []
    self._event_source_offset_tables_lfu = []
    self._event_source_streams = {}

    self._event_timestamp_tables = {}
    self._event_timestamp_tables_lfu = []

    self._zipfile.close()
    self._zipfile = None
    self._is_open = False

    file_renamed = False
    if self._path != self._zipfile_path and os.path.exists(self._zipfile_path):
      # On Windows the file can sometimes be still in use and we have to wait.
      for attempt in range(1, self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS):
        try:
          os.rename(self._zipfile_path, self._path)
          file_renamed = True
          break

        except OSError:
          if attempt == self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS:
            raise
          time.sleep(self._LOCKED_FILE_SLEEP_TIME)

      if file_renamed:
        directory_name = os.path.dirname(self._zipfile_path)
        os.rmdir(directory_name)

    self._path = None
    self._zipfile_path = None

    if self._path != self._zipfile_path and not file_renamed:
      raise IOError(u'Unable to close storage file.')

  def Flush(self):
    """Forces the serialized attribute containers to be written to file.

    Raises:
      IOError: when trying to write to a closed storage file or
               if the event source cannot be serialized.
    """
    if not self._is_open:
      raise IOError(u'Unable to flush a closed storage file.')

    if not self._read_only:
      self._WriteSerializedEventSources()
      self._WriteSerializedEvents()
      self._WriteSerializedEventTags()
      self._WriteSerializedErrors()

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Yields:
      AnalysisReport: analysis report.

    Raises:
      IOError: if the stream cannot be opened.
    """
    for stream_name in self._GetStreamNames():
      if not stream_name.startswith(u'analysis_report_data.'):
        continue

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      for analysis_report in self._ReadAttributeContainersFromStream(
          data_stream, u'analysis_report'):
        yield analysis_report

  def GetErrors(self):
    """Retrieves the errors.

    Yields:
      ExtractionError: error.

    Raises:
      IOError: if a stream is missing.
    """
    for stream_number in range(1, self._error_stream_number):
      stream_name = u'error_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      for error in self._ReadAttributeContainersFromStream(
          data_stream, u'error'):
        yield error

  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      EventObject: event.
    """
    event = self._GetSortedEvent(time_range=time_range)
    while event:
      yield event
      event = self._GetSortedEvent(time_range=time_range)

  def GetEventSourceByIndex(self, index):
    """Retrieves a specific event source.

    Args:
      index (int): event source index.

    Returns:
      EventSource: event source.

    Raises:
      IOError: if a stream is missing.
    """
    stream_number = 1
    while stream_number < self._event_source_stream_number:
      if stream_number <= len(self._event_sources_in_stream):
        number_of_event_sources = self._event_sources_in_stream[
            stream_number - 1]

      else:
        offset_table = self._GetSerializedEventSourceOffsetTable(stream_number)
        number_of_event_sources = offset_table.number_of_offsets
        self._event_sources_in_stream.append(number_of_event_sources)

      if index < number_of_event_sources:
        break

      index -= number_of_event_sources
      stream_number += 1

    if stream_number < self._event_source_stream_number:
      stream_name = u'event_source_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      offset_table = self._GetSerializedEventSourceOffsetTable(stream_number)
      stream_offset = offset_table.GetOffset(index)

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)
      data_stream.SeekEntryAtOffset(index, stream_offset)

      return self._ReadAttributeContainerFromStreamEntry(
          data_stream, u'event_source')

    entry_data = self._event_sources_list.GetAttributeContainerByIndex(index)
    return self._DeserializeAttributeContainer(entry_data, u'event_source')

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      EventSource: event source.

    Raises:
      IOError: if a stream is missing.
    """
    for stream_number in range(1, self._event_source_stream_number):
      stream_name = u'event_source_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      for event_source in self._ReadAttributeContainersFromStream(
          data_stream, u'event_source'):
        yield event_source

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.

    Raises:
      IOError: if a stream is missing.
    """
    for stream_number in range(1, self._event_tag_stream_number):
      stream_name = u'event_tag_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      for event_tag in self._ReadAttributeContainersFromStream(
          data_stream, u'event_tag'):
        yield event_tag

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._analysis_report_stream_number - 1

  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

    Returns:
      int: number of event sources.
    """
    number_of_event_sources = 0
    for stream_number in range(1, self._event_source_stream_number):
      offset_table = self._GetSerializedEventSourceOffsetTable(stream_number)
      number_of_event_sources += offset_table.number_of_offsets

    number_of_event_sources += (
        self._event_sources_list.number_of_attribute_containers)
    return number_of_event_sources

  def GetSessions(self):
    """Retrieves the sessions.

    Yields:
      Session: session attribute container.

    Raises:
      IOError: if a stream is missing or there is a mismatch in session
          identifiers between the session start and completion attribute
          containers.
    """
    for stream_number in range(1, self._last_session):
      stream_name = u'session_start.{0:06d}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      session_start = self._ReadAttributeContainerFromStreamEntry(
          data_stream, u'session_start')

      session_completion = None
      stream_name = u'session_completion.{0:06d}'.format(stream_number)
      if self._HasStream(stream_name):
        data_stream = _SerializedDataStream(
            self._zipfile, self._zipfile_path, stream_name)

        session_completion = self._ReadAttributeContainerFromStreamEntry(
            data_stream, u'session_completion')

      session = sessions.Session()
      session.CopyAttributesFromSessionStart(session_start)
      if session_completion:
        try:
          session.CopyAttributesFromSessionCompletion(session_completion)
        except ValueError:
          raise IOError(
              u'Session identifier mismatch in stream: {0:s}'.format(
                  stream_name))

      yield session

  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      bool: True if the storage contains analysis reports.
    """
    for name in self._GetStreamNames():
      if name.startswith(u'analysis_report_data.'):
        return True

    return False

  def HasErrors(self):
    """Determines if a storage contains extraction errors.

    Returns:
      bool: True if the storage contains extraction errors.
    """
    for name in self._GetStreamNames():
      if name.startswith(u'error_data.'):
        return True

    return False

  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """
    for name in self._GetStreamNames():
      if name.startswith(u'event_tag_data.'):
        return True

    return False

  def Open(self, path=None, read_only=True, **unused_kwargs):
    """Opens the storage.

    Args:
      path (Optional[str]): path of the storage file.
      read_only (Optional[bool]): True if the file should be opened in
          read-only mode.

    Raises:
      IOError: if the storage file is already opened.
      ValueError: if path is missing.
    """
    if self._is_open:
      raise IOError(u'Storage file already opened.')

    if not path:
      raise ValueError(u'Missing path.')

    self._OpenZIPFile(path, read_only)
    self._OpenRead()

    if not read_only:
      self._OpenWrite()

  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
    """
    for stream_number in range(1, self._last_preprocess):
      stream_name = u'preprocess.{0:06d}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      system_configuration = self._ReadAttributeContainerFromStreamEntry(
          data_stream, u'preprocess')

      knowledge_base.ReadSystemConfigurationArtifact(
          stream_number, system_configuration)

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocess
               information or the storage file is closed or read-only or
               if the preprocess information stream already exists.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Preprocess information not supported by storage type.')

    stream_name = u'preprocess.{0:06d}'.format(self._last_preprocess)
    if self._HasStream(stream_name):
      raise IOError(u'preprocess information: {0:06d} already exists.'.format(
          self._last_preprocess))

    system_configuration = knowledge_base.GetSystemConfigurationArtifact()

    preprocess_data = self._SerializeAttributeContainer(system_configuration)

    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)
    data_stream.WriteInitialize()
    data_stream.WriteEntry(preprocess_data)
    data_stream.WriteFinalize()

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    self.Flush()

    self._WriteSessionCompletion(session_completion)
    self._last_session += 1

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    self._WriteSessionStart(session_start)

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    self.Flush()

    self._WriteTaskCompletion(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    self._WriteTaskStart(task_start)


class ZIPStorageFileReader(interface.FileStorageReader):
  """Class that implements the ZIP-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(ZIPStorageFileReader, self).__init__(path)
    self._storage_file = ZIPStorageFile()
    self._storage_file.Open(path=path)


class ZIPStorageFileWriter(interface.StorageWriter):
  """Class that implements the ZIP-based storage file writer."""

  def __init__(
      self, session, output_file, buffer_size=0,
      storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      output_file (str): path to the output file.
      buffer_size (Optional[int]): estimated size of a protobuf file.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(ZIPStorageFileWriter, self).__init__(
        session, storage_type=storage_type, task=task)
    self._buffer_size = buffer_size
    self._merge_task_storage_path = u''
    self._output_file = output_file
    self._storage_file = None
    self._serializers_profiler = None
    self._task_storage_path = None

  def _UpdateCounters(self, event):
    """Updates the counters.

    Args:
      event: an event (instance of EventObject).
    """
    self._session.parsers_counter[u'total'] += 1

    # Here we want the name of the parser or plugin not the parser chain.
    parser_name = getattr(event, u'parser', u'')
    _, _, parser_name = parser_name.rpartition(u'/')
    if not parser_name:
      parser_name = u'N/A'
    self._session.parsers_counter[parser_name] += 1

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report: an analysis report object (instance of AnalysisReport).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    for event_tag in analysis_report.GetTags():
      self.AddEventTag(event_tag)

    self._storage_file.AddAnalysisReport(analysis_report)

    report_identifier = analysis_report.plugin_name
    self._session.analysis_reports_counter[u'total'] += 1
    self._session.analysis_reports_counter[report_identifier] += 1
    self.number_of_analysis_reports += 1

  def AddError(self, error):
    """Adds an error.

    Args:
      error: an error object (instance of AnalysisError or ExtractionError).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    self._storage_file.AddError(error)
    self.number_of_errors += 1

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event: an event (instance of EventObject).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    self._storage_file.AddEvent(event)
    self.number_of_events += 1

    self._UpdateCounters(event)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source: an event source object (instance of EventSource).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    self._storage_file.AddEventSource(event_source)
    self.number_of_event_sources += 1

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag: an event tag object (instance of EventTag).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    self._storage_file.AddEventTag(event_tag)

    self._session.event_labels_counter[u'total'] += 1
    for label in event_tag.labels:
      self._session.event_labels_counter[label] += 1
    self.number_of_event_tags += 1

  def CheckTaskReadyForMerge(self, task):
    """Checks if a task is ready for merging with this session storage.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task is ready to be merged.

    Raises:
      IOError: if the storage type is not supported or
               if the temporary path for the task storage does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    if not self._merge_task_storage_path:
      raise IOError(u'Missing merge task storage path.')

    storage_file_path = os.path.join(
        self._merge_task_storage_path, u'{0:s}.plaso'.format(task.identifier))

    try:
      stat_info = os.stat(storage_file_path)
    except (IOError, OSError):
      return False

    task.storage_file_size = stat_info.st_size
    return True

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    self._storage_file.Close()
    self._storage_file = None

  def CreateTaskStorage(self, task):
    """Creates a task storage.

    The task storage is used to store attributes created by the task.

    Args:
      task(Task): task.

    Returns:
      StorageWriter: storage writer.

    Raises:
      IOError: if the storage type is not supported or
               if the temporary path for the task storage does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    if not self._task_storage_path:
      raise IOError(u'Missing task storage path.')

    storage_file_path = os.path.join(
        self._task_storage_path, u'{0:s}.plaso'.format(task.identifier))

    return ZIPStorageFileWriter(
        self._session, storage_file_path, buffer_size=self._buffer_size,
        storage_type=definitions.STORAGE_TYPE_TASK, task=task)

  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to read from closed storage writer.')

    return self._storage_file.GetEvents(time_range=time_range)

  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to read from closed storage writer.')

    event_source = self._storage_file.GetEventSourceByIndex(
        self._first_written_event_source_index)

    if event_source:
      self._written_event_source_index = (
          self._first_written_event_source_index + 1)
    return event_source

  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to read from closed storage writer.')

    event_source = self._storage_file.GetEventSourceByIndex(
        self._written_event_source_index)
    if event_source:
      self._written_event_source_index += 1
    return event_source

  def Open(self):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
    """
    if self._storage_file:
      raise IOError(u'Storage writer already opened.')

    if self._storage_type == definitions.STORAGE_TYPE_TASK:
      self._storage_file = gzip_file.GZIPStorageFile(
          storage_type=self._storage_type)
    else:
      self._storage_file = ZIPStorageFile(
          maximum_buffer_size=self._buffer_size,
          storage_type=self._storage_type)

    if self._serializers_profiler:
      self._storage_file.SetSerializersProfiler(self._serializers_profiler)

    self._storage_file.Open(path=self._output_file, read_only=False)

    self._first_written_event_source_index = (
        self._storage_file.GetNumberOfEventSources())
    self._written_event_source_index = self._first_written_event_source_index

  def PrepareMergeTaskStorage(self, task):
    """Prepares a task storage for merging.

    Args:
      task (Task): unique identifier of the task.

    Raises:
      IOError: if the storage type is not supported or
               if the temporary path for the task storage does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    if not self._task_storage_path:
      raise IOError(u'Missing task storage path.')

    storage_file_path = os.path.join(
        self._task_storage_path, u'{0:s}.plaso'.format(task.identifier))

    merge_storage_file_path = os.path.join(
        self._merge_task_storage_path, u'{0:s}.plaso'.format(task.identifier))

    try:
      os.rename(storage_file_path, merge_storage_file_path)
    except OSError as exception:
      raise IOError((
          u'Unable to rename task storage file: {0:s} with error: '
          u'{1:s}').format(storage_file_path, exception))

  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to read from closed storage writer.')

    return self._storage_file.ReadPreprocessingInformation(knowledge_base)

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profile.
    """
    self._serializers_profiler = serializers_profiler
    if self._storage_file:
      self._storage_file.SetSerializersProfiler(serializers_profiler)

  def StartMergeTaskStorage(self, task):
    """Starts a merge of a task storage with the session storage.

    Args:
      task (Task): task.

    Returns:
      StorageMergeReader: storage merge reader of the task storage.

    Raises:
      IOError: if the storage file cannot be opened or
               if the storage type is not supported or
               if the temporary path for the task storage does not exist or
               if the temporary path for the task storage doe not refers to
               a file.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    if not self._merge_task_storage_path:
      raise IOError(u'Missing merge task storage path.')

    storage_file_path = os.path.join(
        self._merge_task_storage_path, u'{0:s}.plaso'.format(task.identifier))

    if not os.path.isfile(storage_file_path):
      raise IOError(u'Merge task storage path is not a file.')

    return gzip_file.GZIPStorageMergeReader(self, storage_file_path)

  def StartTaskStorage(self):
    """Creates a temporary path for the task storage.

    Raises:
      IOError: if the storage type is not supported or
               if the temporary path for the task storage already exists.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    if self._task_storage_path:
      raise IOError(u'Task storage path already exists.')

    output_directory = os.path.dirname(self._output_file)
    self._task_storage_path = tempfile.mkdtemp(dir=output_directory)

    self._merge_task_storage_path = os.path.join(
        self._task_storage_path, u'merge')
    os.mkdir(self._merge_task_storage_path)

  def StopTaskStorage(self, abort=False):
    """Removes the temporary path for the task storage.

    Args:
      abort (bool): True to indicated the stop is issued on abort.

    Raises:
      IOError: if the storage type is not supported or
               if the temporary path for the task storage does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    if not self._task_storage_path:
      raise IOError(u'Missing task storage path.')

    if os.path.isdir(self._merge_task_storage_path):
      if abort:
        shutil.rmtree(self._merge_task_storage_path)
      else:
        os.rmdir(self._merge_task_storage_path)

    if os.path.isdir(self._task_storage_path):
      if abort:
        shutil.rmtree(self._task_storage_path)
      else:
        os.rmdir(self._task_storage_path)

    self._merge_task_storage_path = None
    self._task_storage_path = None

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocessing
               information or when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Preprocessing information not supported by storage type.')

    self._storage_file.WritePreprocessingInformation(knowledge_base)

  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
               when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    self._session.aborted = aborted
    session_completion = self._session.CreateSessionCompletion()
    self._storage_file.WriteSessionCompletion(session_completion)

  def WriteSessionStart(self):
    """Writes session start information.

    Raises:
      IOError: if the storage type is not supported or
               when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Unsupported storage type.')

    session_start = self._session.CreateSessionStart()
    self._storage_file.WriteSessionStart(session_start)

  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
               when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Unsupported storage type.')

    self._task.aborted = aborted
    task_completion = self._task.CreateTaskCompletion()
    self._storage_file.WriteTaskCompletion(task_completion)

  def WriteTaskStart(self):
    """Writes task start information.

    Raises:
      IOError: if the storage type is not supported or
               when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Unsupported storage type.')

    task_start = self._task.CreateTaskStart()
    self._storage_file.WriteTaskStart(task_start)
