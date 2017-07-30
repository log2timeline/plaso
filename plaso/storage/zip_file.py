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

+ Version information

Deprecated in version 20170121:
* event_tag_index.#
  The event tag index streams contain the stream offset to the serialized
  event tag objects.

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
from plaso.storage import identifiers
from plaso.storage import interface
from plaso.storage import gzip_file


class _EventsHeap(object):
  """Events heap."""

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

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    event_identifier = event.GetIdentifier()
    heap_values = (
        event.timestamp, event_identifier.stream_number,
        event_identifier.entry_index, event)
    heapq.heappush(self._heap, heap_values)


class _SerializedEventsHeap(object):
  """Serialized events heap.

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
      tuple: contains:

        int: event timestamp or None if the heap is empty
        bytes: serialized event data or None if the heap is empty
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


class _SerializedDataStream(object):
  """Serialized data stream."""

  _DATA_ENTRY = construct.Struct(
      u'data_entry',
      construct.ULInt32(u'size'))
  _DATA_ENTRY_SIZE = _DATA_ENTRY.sizeof()

  # The default maximum serialized data size (40 MiB).
  DEFAULT_MAXIMUM_DATA_SIZE = 40 * 1024 * 1024

  def __init__(
      self, zip_file, storage_file_path, stream_name,
      maximum_data_size=DEFAULT_MAXIMUM_DATA_SIZE):
    """Initializes a serialized data stream.

    Args:
      zip_file (zipfile.ZipFile): ZIP file that contains the stream.
      storage_file_path (str): path to the storage file.
      stream_name (str): name of the stream.
      maximum_data_size (Optional[int]): maximum data size of the stream.
    """
    super(_SerializedDataStream, self).__init__()
    self._entry_index = 0
    self._file_object = None
    self._maximum_data_size = maximum_data_size
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
      raise IOError(u'Unable to read data entry with error: {0:s}'.format(
          exception))

    if data_entry.size > self._maximum_data_size:
      raise IOError(u'Unable to read data entry size value out of bounds.')

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
      IOError: if the serialized data stream was not opened for writing or
          the entry cannot be written to the serialized data stream.
    """
    if not self._file_object:
      raise IOError(u'Unable to write to closed serialized data stream.')

    data_size = len(data)
    # TODO: Fix maximum size limit handling to create new stream.
    # data_end_offset = (
    #    self._file_object.tell() + self._DATA_ENTRY_SIZE + data_size)
    # if data_end_offset > self._maximum_data_size:
    #  raise IOError(u'Unable to write data entry size value out of bounds.')

    data_size = construct.ULInt32(u'size').build(data_size)
    self._file_object.write(data_size)
    self._file_object.write(data)

    return self._file_object.tell()

  def WriteFinalize(self):
    """Finalize the write of a serialized data stream.

    Writes the temporary file with the serialized data to the zip file.

    Returns:
      int: offset of the entry within the temporary file.

    Raises:
      IOError: if the serialized data stream was not opened for writing or
          the serialized data stream cannot be written.
    """
    if not self._file_object:
      raise IOError(u'Unable to write to closed serialized data stream.')

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
      IOError: if the serialized data stream is already opened or
          cannot be written.
    """
    if self._file_object:
      raise IOError(u'Serialized data stream already opened.')

    stream_file_path = os.path.join(self._path, self._stream_name)
    self._file_object = open(stream_file_path, 'wb')
    if platform_specific.PlatformIsWindows():
      file_handle = self._file_object.fileno()
      platform_specific.DisableWindowsFileHandleInheritance(file_handle)

    return self._file_object.tell()


class _SerializedDataOffsetTable(object):
  """Serialized data offset table."""

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
  """Serialized data timestamp table."""

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


class _StorageMetadata(object):
  """Storage metadata.

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
  """Storage metadata reader."""

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
  """ZIP-based storage file.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  NEXT_AVAILABLE_ENTRY = -1

  # The format version.
  _FORMAT_VERSION = 20170121

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _COMPATIBLE_FORMAT_VERSION = 20170121

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
    self._event_offset_tables = {}
    self._event_offset_tables_lfu = []
    self._event_stream_number = 1
    self._event_streams = {}
    self._event_source_offset_tables = {}
    self._event_source_offset_tables_lfu = []
    self._event_source_streams = {}
    self._event_sources_in_stream = []
    self._event_tag_index = None
    self._event_tag_offset_tables = {}
    self._event_tag_offset_tables_lfu = []
    self._event_tag_streams = {}
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
    self._stream_numbers = {}
    self._path = None
    self._zipfile = None
    self._zipfile_path = None

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

  def _AddAttributeContainer(self, container_type, attribute_container):
    """Adds an atttibute container.

    Args:
      container_type (str): attribute container type.
      attribute_container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the attribute container cannot be serialized.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    container_list = self._GetSerializedAttributeContainerList(
        container_type)

    stream_number = self._stream_numbers[container_type]
    identifier = identifiers.SerializedStreamIdentifier(
        stream_number, container_list.number_of_attribute_containers)
    attribute_container.SetIdentifier(identifier)

    # We try to serialize the error first, so we can skip some
    # processing if it is invalid.
    serialized_data = self._SerializeAttributeContainer(attribute_container)

    container_list.PushAttributeContainer(serialized_data)

    if container_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(container_type)

  def _BuildEventTagIndex(self):
    """Builds the event tag index.

    Raises:
      IOError: if a stream is missing.
    """
    self._event_tag_index = {}
    for event_tag in self.GetEventTags():
      event_identifier = event_tag.GetEventIdentifier()
      lookup_key = event_identifier.CopyToString()
      self._event_tag_index[lookup_key] = event_tag.GetIdentifier()

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

    self._event_heap.PushEvent(event)

    reference_timestamp = event.timestamp
    while event.timestamp == reference_timestamp:
      event = self._GetEvent(stream_number)
      if not event:
        break

      self._event_heap.PushEvent(event)

  def _GetEvent(self, stream_number, entry_index=NEXT_AVAILABLE_ENTRY):
    """Reads an event from a specific stream.

    Args:
      stream_number (int): number of the serialized event stream.
      entry_index (Optional[int]): number of the serialized event within
          the stream, where NEXT_AVAILABLE_ENTRY represents the next available
          event.

    Returns:
      EventObject: event or None.
    """
    event_data, entry_index = self._GetEventSerializedData(
        stream_number, entry_index=entry_index)
    if not event_data:
      return

    event = self._DeserializeAttributeContainer(u'event', event_data)
    if event:
      event_identifier = identifiers.SerializedStreamIdentifier(
          stream_number, entry_index)
      event.SetIdentifier(event_identifier)
    return event

  def _GetEventSerializedData(
      self, stream_number, entry_index=NEXT_AVAILABLE_ENTRY):
    """Retrieves specific event serialized data.

    By default the first available entry in the specific serialized stream
    is read, however any entry can be read using the index stream.

    Args:
      stream_number (int): number of the serialized event stream.
      entry_index (Optional[int]): number of the serialized event within
          the stream, where NEXT_AVAILABLE_ENTRY represents the next available
          event.

    Returns:
      tuple: contains:

        bytes: event serialized data.
        int: entry index of the event within the stream.

    Raises:
      IOError: if the stream cannot be opened.
      ValueError: if the stream number or entry index is out of bounds.
    """
    if stream_number is None:
      raise ValueError(u'Invalid stream number.')

    if entry_index is None:
      raise ValueError(u'Invalid entry index.')

    if stream_number < 1 or stream_number > self._event_stream_number:
      raise ValueError(u'Stream number: {0:d} out of bounds.'.format(
          stream_number))

    if entry_index < self.NEXT_AVAILABLE_ENTRY:
      raise ValueError(u'Entry index: {0:d} out of bounds.'.format(
          entry_index))

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

  def _GetEventSource(self, stream_number, entry_index=NEXT_AVAILABLE_ENTRY):
    """Reads an event source from a specific stream.

    Args:
      stream_number (int): number of the serialized event source stream.
      entry_index (Optional[int]): number of the serialized event source
          within the stream, where NEXT_AVAILABLE_ENTRY represents the next
          available event
          source.

    Returns:
      EventSource: event source or None.
    """
    event_source_data, entry_index = self._GetEventSourceSerializedData(
        stream_number, entry_index=entry_index)
    if not event_source_data:
      return

    event_source = self._DeserializeAttributeContainer(
        u'event_source', event_source_data)
    if event_source:
      event_source_identifier = identifiers.SerializedStreamIdentifier(
          stream_number, entry_index)
      event_source.SetIdentifier(event_source_identifier)
    return event_source

  def _GetEventSourceSerializedData(
      self, stream_number, entry_index=NEXT_AVAILABLE_ENTRY):
    """Retrieves specific event source serialized data.

    By default the first available entry in the specific serialized stream
    is read, however any entry can be read using the index stream.

    Args:
      stream_number (int): number of the serialized event source stream.
      entry_index (Optional[int]): number of the serialized event source
          within the stream, where NEXT_AVAILABLE_ENTRY represents the next
          available event source.

    Returns:
      tuple: contains:

        bytes: event source serialized data.
        int: entry index of the event source within the stream.

    Raises:
      IOError: if the stream cannot be opened.
      ValueError: if the stream number or entry index is out of bounds.
    """
    event_source_stream_number = self._stream_numbers[u'event_source']

    if stream_number < 1 or stream_number > event_source_stream_number:
      raise ValueError(u'Stream number out of bounds.')

    if entry_index < self.NEXT_AVAILABLE_ENTRY:
      raise ValueError(u'Entry index out of bounds.')

    if stream_number == event_source_stream_number:
      if entry_index < 0:
        raise ValueError(u'Entry index out of bounds.')

      event_source_data = self._GetSerializedAttributeContainerByIndex(
          u'event_source', entry_index)
      return event_source_data, entry_index

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

  def _GetEventTag(self, stream_number, entry_index=NEXT_AVAILABLE_ENTRY):
    """Reads an event tag from a specific stream.

    Args:
      stream_number (int): number of the serialized event tag stream.
      entry_index (Optional[int]): number of the serialized event tag
          within the stream, where NEXT_AVAILABLE_ENTRY represents
          the next available event tag.

    Returns:
      EventTag: event tag or None.
    """
    event_tag_data, entry_index = self._GetEventTagSerializedData(
        stream_number, entry_index=entry_index)
    if not event_tag_data:
      return

    event_tag = self._DeserializeAttributeContainer(
        u'event_tag', event_tag_data)
    if event_tag:
      event_tag_identifier = identifiers.SerializedStreamIdentifier(
          stream_number, entry_index)
      event_tag.SetIdentifier(event_tag_identifier)

      event_identifier = identifiers.SerializedStreamIdentifier(
          event_tag.event_stream_number, event_tag.event_entry_index)
      event_tag.SetEventIdentifier(event_identifier)

      del event_tag.event_stream_number
      del event_tag.event_entry_index

    return event_tag

  def _GetEventTagByIdentifier(self, event_identifier):
    """Retrieves an event tag by the event identifier.

    Args:
      event_identifier (AttributeContainerIdentifier): event attribute
          container identifier.

    Returns:
      EventTag: event tag or None.

    Raises:
      IOError: if the event tag data stream cannot be opened.
    """
    if not self._event_tag_index:
      self._BuildEventTagIndex()

    lookup_key = event_identifier.CopyToString()
    event_tag_identifier = self._event_tag_index.get(lookup_key, None)
    if not event_tag_identifier:
      return

    return self._GetEventTag(
        event_tag_identifier.stream_number,
        entry_index=event_tag_identifier.entry_index)

  def _GetEventTagSerializedData(
      self, stream_number, entry_index=NEXT_AVAILABLE_ENTRY):
    """Retrieves specific event tag serialized data.

    By default the first available entry in the specific serialized stream
    is read, however any entry can be read using the index stream.

    Args:
      stream_number (int): number of the serialized event tag stream.
      entry_index (Optional[int]): number of the serialized event tag
          within the stream, where NEXT_AVAILABLE_ENTRY represents
          the next available event tag.

    Returns:
      tuple: contains:

        bytes: event tag serialized data.
        int: entry index of the event tag within the stream.

    Raises:
      IOError: if the stream cannot be opened.
      ValueError: if the stream number or entry index is out of bounds.
    """
    event_tag_stream_number = self._stream_numbers[u'event_tag']

    if stream_number < 1 or stream_number > event_tag_stream_number:
      raise ValueError(u'Stream number out of bounds.')

    if entry_index < self.NEXT_AVAILABLE_ENTRY:
      raise ValueError(u'Entry index out of bounds.')

    if stream_number == event_tag_stream_number:
      if entry_index < 0:
        raise ValueError(u'Entry index out of bounds.')

      event_tag_data = self._GetSerializedAttributeContainerByIndex(
          u'event_tag', entry_index)
      return event_tag_data, entry_index

    try:
      data_stream = self._GetSerializedEventTagStream(stream_number)
    except IOError as exception:
      logging.error((
          u'Unable to retrieve serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    if entry_index >= 0:
      try:
        offset_table = self._GetSerializedEventTagOffsetTable(stream_number)
        stream_offset = offset_table.GetOffset(entry_index)
      except (IOError, IndexError):
        logging.error((
            u'Unable to read entry index: {0:d} from serialized data stream: '
            u'{1:d}').format(entry_index, stream_number))
        return None, None

      data_stream.SeekEntryAtOffset(entry_index, stream_offset)

    event_tag_entry_index = data_stream.entry_index
    try:
      event_tag_data = data_stream.ReadEntry()
    except IOError as exception:
      logging.error((
          u'Unable to read entry from serialized data steam: {0:d} '
          u'with error: {1:s}.').format(stream_number, exception))
      return None, None

    return event_tag_data, event_tag_entry_index

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

  def _GetSerializedEventTagStream(self, stream_number):
    """Retrieves the serialized event tag stream.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataStream: serialized data stream.

    Raises:
      IOError: if the stream cannot be opened.
    """
    return self._GetSerializedDataStream(
        self._event_tag_streams, u'event_tag_data', stream_number)

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

  def _GetSerializedEventTagOffsetTable(self, stream_number):
    """Retrieves the serialized event tag stream offset table.

    Args:
      stream_number (int): number of the stream.

    Returns:
      _SerializedDataOffsetTable: serialized data offset table.

    Raises:
      IOError: if the stream cannot be opened.
    """
    return self._GetSerializedDataOffsetTable(
        self._event_tag_offset_tables, self._event_tag_offset_tables_lfu,
        u'event_tag_index', stream_number)

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

    event_identifier = event.GetIdentifier()
    event.tag = self._GetEventTagByIdentifier(event_identifier)
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
      entry_index = self.NEXT_AVAILABLE_ENTRY
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
          timestamp_compare = timestamp_table.GetTimestamp(
              self.NEXT_AVAILABLE_ENTRY)
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

        self._event_heap.PushEvent(event)

        reference_timestamp = event.timestamp
        while event.timestamp == reference_timestamp:
          event = self._GetEvent(stream_number)
          if not event:
            break

          self._event_heap.PushEvent(event)

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

    # TODO: create a single function to determin last stream numbers.
    self._stream_numbers[u'extraction_error'] = self._GetLastStreamNumber(
        u'error_data.')
    self._event_stream_number = self._GetLastStreamNumber(u'event_data.')

    self._stream_numbers[u'event_source'] = self._GetLastStreamNumber(
        u'event_source_data.')
    self._stream_numbers[u'event_tag'] = self._GetLastStreamNumber(
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
      path (str): path to the ZIP file.
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
    return self._DeserializeAttributeContainer(container_type, entry_data)

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

  def _WriteSerializedAttributeContainerList(self, container_type):
    """Writes a serialized attribute container list.

    Args:
      container_type (str): attribute container type.
    """
    container_list = self._GetSerializedAttributeContainerList(container_type)
    if not container_list.data_size:
      return

    stream_number = self._stream_numbers[container_type]

    stream_name = u'{0:s}_index.{1:06d}'.format(container_type, stream_number)
    offset_table = _SerializedDataOffsetTable(self._zipfile, stream_name)

    stream_name = u'{0:s}_data.{1:06d}'.format(container_type, stream_number)
    data_stream = _SerializedDataStream(
        self._zipfile, self._zipfile_path, stream_name)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    entry_data_offset = data_stream.WriteInitialize()

    try:
      for _ in range(container_list.number_of_attribute_containers):
        serialized_data = container_list.PopAttributeContainer()

        offset_table.AddOffset(entry_data_offset)

        entry_data_offset = data_stream.WriteEntry(serialized_data)

    except:
      data_stream.WriteAbort()

      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(u'write')

      raise

    offset_table.Write()
    data_stream.WriteFinalize()

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'write')

    self._stream_numbers[container_type] = stream_number + 1

    container_list.Empty()

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

    analysis_report_identifier = identifiers.SerializedStreamIdentifier(
        self._analysis_report_stream_number, 0)
    analysis_report.SetIdentifier(analysis_report_identifier)

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
    self._AddAttributeContainer(u'extraction_error', error)

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

    event_identifier = identifiers.SerializedStreamIdentifier(
        self._event_stream_number,
        self._serialized_events_heap.number_of_events)
    event.SetIdentifier(event_identifier)

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
    self._AddAttributeContainer(u'event_source', event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    If the event referenced by the tag is already tagged, the comment
    and labels will be appended to the existing tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the event tag cannot be serialized or
          if the event tag event identifier type is not supported.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    event_identifier = event_tag.GetEventIdentifier()
    if not isinstance(
        event_identifier, identifiers.SerializedStreamIdentifier):
      raise IOError(u'Unsupported event identifier type: {0:s}'.format(
          type(event_identifier)))

    container_list = self._GetSerializedAttributeContainerList(u'event_tag')

    stream_number = self._stream_numbers[u'event_tag']
    event_tag_identifier = identifiers.SerializedStreamIdentifier(
        stream_number, container_list.number_of_attribute_containers)
    event_tag.SetIdentifier(event_tag_identifier)

    # Check if the event has already been tagged on a previous occasion,
    # we need to append the event tag any existing event tag.
    stored_event_tag = self._GetEventTagByIdentifier(event_identifier)

    if stored_event_tag:
      event_tag.AddComment(stored_event_tag.comment)
      event_tag.AddLabels(stored_event_tag.labels)

    event_tag.event_stream_number = event_identifier.stream_number
    event_tag.event_entry_index = event_identifier.entry_index

    # TODO: update event tag index value.
    lookup_key = event_identifier.CopyToString()
    self._event_tag_index[lookup_key] = event_tag_identifier

    # We try to serialize the event tag first, so we can skip some
    # processing if it is invalid.
    event_tag_data = self._SerializeAttributeContainer(event_tag)

    container_list.PushAttributeContainer(event_tag_data)

    if container_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(u'event_tag')

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

    for event_tag in event_tags:
      self.AddEventTag(event_tag)

  @classmethod
  def CheckSupportedFormat(cls, path):
    """Checks is the storage file format is supported.

    Args:
      path (str): path to the storage file.

    Returns:
      bool: True if the format is supported.
    """
    try:
      zip_file = zipfile.ZipFile(
          path, mode=u'r', compression=zipfile.ZIP_DEFLATED, allowZip64=True)

      # TODO: check metadata.

      zip_file.close()
      result = True

    except zipfile.BadZipfile:
      result = False

    return result

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

    self._event_tag_offset_tables = []
    self._event_tag_offset_tables_lfu = []
    self._event_tag_streams = {}

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
      self._WriteSerializedAttributeContainerList(u'event_source')
      self._WriteSerializedEvents()
      self._WriteSerializedAttributeContainerList(u'event_tag')
      self._WriteSerializedAttributeContainerList(u'extraction_error')

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
        # TODO: add SetIdentifier.
        yield analysis_report

  def GetErrors(self):
    """Retrieves the errors.

    Yields:
      ExtractionError: error.

    Raises:
      IOError: if a stream is missing.
    """
    error_stream_number = self._stream_numbers[u'extraction_error']

    for stream_number in range(1, error_stream_number):
      stream_name = u'error_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      generator = self._ReadAttributeContainersFromStream(data_stream, u'error')
      for entry_index, error in enumerate(generator):
        error_identifier = identifiers.SerializedStreamIdentifier(
            stream_number, entry_index)
        error.SetIdentifier(error_identifier)
        yield error

  def GetEvents(self):
    """Retrieves the events.

    Yields:
      EventObject: event.
    """
    for stream_number in range(1, self._event_stream_number):
      stream_name = u'event_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      generator = self._ReadAttributeContainersFromStream(
          data_stream, u'event')
      for entry_index, event in enumerate(generator):
        event_identifier = identifiers.SerializedStreamIdentifier(
            stream_number, entry_index)
        event.SetIdentifier(event_identifier)
        yield event

  def GetEventSourceByIndex(self, index):
    """Retrieves a specific event source.

    Args:
      index (int): event source index.

    Returns:
      EventSource: event source.

    Raises:
      IOError: if a stream is missing.
    """
    event_source_stream_number = self._stream_numbers[u'event_source']

    stream_number = 1
    while stream_number < event_source_stream_number:
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

    if stream_number < event_source_stream_number:
      stream_name = u'event_source_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      offset_table = self._GetSerializedEventSourceOffsetTable(stream_number)
      stream_offset = offset_table.GetOffset(index)

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)
      data_stream.SeekEntryAtOffset(index, stream_offset)

      event_source = self._ReadAttributeContainerFromStreamEntry(
          data_stream, u'event_source')
      if event_source:
        event_source_identifier = identifiers.SerializedStreamIdentifier(
            stream_number, index)
        event_source.SetIdentifier(event_source_identifier)
      return event_source

    serialized_data = self._GetSerializedAttributeContainerByIndex(
        u'event_source', index)
    event_source = self._DeserializeAttributeContainer(
        u'event_source', serialized_data)
    if event_source:
      event_source_identifier = identifiers.SerializedStreamIdentifier(
          stream_number, index)
      event_source.SetIdentifier(event_source_identifier)
    return event_source

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      EventSource: event source.

    Raises:
      IOError: if a stream is missing.
    """
    event_source_stream_number = self._stream_numbers[u'event_source']

    for stream_number in range(1, event_source_stream_number):
      stream_name = u'event_source_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      generator = self._ReadAttributeContainersFromStream(
          data_stream, u'event_source')
      for entry_index, event_source in enumerate(generator):
        event_source_identifier = identifiers.SerializedStreamIdentifier(
            stream_number, entry_index)
        event_source.SetIdentifier(event_source_identifier)
        yield event_source

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.

    Raises:
      IOError: if a stream is missing.
    """
    event_tag_stream_number = self._stream_numbers[u'event_tag']

    for stream_number in range(1, event_tag_stream_number):
      stream_name = u'event_tag_data.{0:06}'.format(stream_number)
      if not self._HasStream(stream_name):
        raise IOError(u'No such stream: {0:s}'.format(stream_name))

      data_stream = _SerializedDataStream(
          self._zipfile, self._zipfile_path, stream_name)

      generator = self._ReadAttributeContainersFromStream(
          data_stream, u'event_tag')
      for entry_index, event_tag in enumerate(generator):
        event_tag_identifier = identifiers.SerializedStreamIdentifier(
            stream_number, entry_index)
        event_tag.SetIdentifier(event_tag_identifier)

        event_identifier = identifiers.SerializedStreamIdentifier(
            event_tag.event_stream_number, event_tag.event_entry_index)
        event_tag.SetEventIdentifier(event_identifier)

        del event_tag.event_stream_number
        del event_tag.event_entry_index

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
    event_source_stream_number = self._stream_numbers[u'event_source']

    number_of_event_sources = 0
    for stream_number in range(1, event_source_stream_number):
      offset_table = self._GetSerializedEventSourceOffsetTable(stream_number)
      number_of_event_sources += offset_table.number_of_offsets

    number_of_event_sources += self._GetNumberOfSerializedAttributeContainers(
        u'event_sources')
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

  def GetSortedEvents(self, time_range=None):
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
      path (Optional[str]): path to the storage file.
      read_only (Optional[bool]): True if the file should be opened in
          read-only mode.

    Raises:
      IOError: if the storage file is already opened.
      ValueError: if path is missing.
    """
    if not path:
      raise ValueError(u'Missing path.')

    if self._is_open:
      raise IOError(u'Storage file already opened.')

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

      # TODO: replace stream_number by session_identifier.
      knowledge_base.ReadSystemConfigurationArtifact(
          system_configuration, session_identifier=stream_number)

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
  """ZIP-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(ZIPStorageFileReader, self).__init__(path)
    self._storage_file = ZIPStorageFile()
    self._storage_file.Open(path=path)


class ZIPStorageFileWriter(interface.FileStorageWriter):
  """ZIP-based storage file writer."""

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
        session, output_file, storage_type=storage_type, task=task)
    self._buffer_size = buffer_size

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      BaseFileStorage: storage file.
    """
    if self._storage_type == definitions.STORAGE_TYPE_TASK:
      return gzip_file.GZIPStorageFile(storage_type=self._storage_type)

    return ZIPStorageFile(
        maximum_buffer_size=self._buffer_size,
        storage_type=self._storage_type)

  def _CreateTaskStorageMergeReader(self, path):
    """Creates a task storage merge reader.

    Args:
      path (str): path to the task storage file that should be merged.

    Returns:
      StorageMergeReader: storage merge reader.
    """
    return gzip_file.GZIPStorageMergeReader(self, path)

  def _CreateTaskStorageWriter(self, path, task):
    """Creates a task storage writer.

    Args:
      path (str): path to the storage file.
      task (Task): task.

    Returns:
      StorageWriter: storage writer.
    """
    return ZIPStorageFileWriter(
        self._session, path, buffer_size=self._buffer_size,
        storage_type=definitions.STORAGE_TYPE_TASK, task=task)
