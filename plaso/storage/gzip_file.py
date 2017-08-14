# -*- coding: utf-8 -*-
"""gzip-based storage.

Only supports task storage at the moment.
"""

import gzip
import os
import time

from plaso.lib import definitions
from plaso.lib import platform_specific
from plaso.storage import event_heaps
from plaso.storage import identifiers
from plaso.storage import interface


class GZIPStorageFile(interface.BaseFileStorage):
  """gzip-based storage file."""

  # pylint: disable=abstract-method

  _COMPRESSION_LEVEL = 9

  _DATA_BUFFER_SIZE = 1 * 1024 * 1024

  def __init__(self, storage_type=definitions.STORAGE_TYPE_TASK):
    """Initializes a storage.

    Args:
      storage_type (Optional[str]): storage type.

    Raises:
      ValueError: if the storage type is not supported.
    """
    if storage_type != definitions.STORAGE_TYPE_TASK:
      raise ValueError(u'Unsupported storage type: {0:s}.'.format(
          storage_type))

    super(GZIPStorageFile, self).__init__()
    self._attribute_containers = {}
    self._gzip_file = None
    self._number_of_containers = 0

  def _AddAttributeContainer(self, attribute_container):
    """Adds an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.
    """
    container_list = self._GetAttributeContainerList(
        attribute_container.CONTAINER_TYPE)

    container_list.append(attribute_container)

  def _GetAttributeContainerList(self, container_type):
    """Retrieves an attribute container list.

    Args:
      container_type (str): attribute container type.

    Returns:
      list[AttributeContainer]: attribute container list.
    """
    if container_type not in self._attribute_containers:
      self._attribute_containers[container_type] = []

    return self._attribute_containers[container_type]

  def _OpenRead(self):
    """Opens the storage file for reading."""
    # Do not use gzip.readlines() here since it can consume a large amount
    # of memory.
    data_buffer = self._gzip_file.read(self._DATA_BUFFER_SIZE)
    while data_buffer:
      lines = data_buffer.splitlines(True)
      data_buffer = b''
      for index, line in enumerate(lines):
        if line.endswith(b'\n'):
          attribute_container = self._DeserializeAttributeContainer(
              u'attribute_container', line)
          self._AddAttributeContainer(attribute_container)
        else:
          data_buffer = b''.join(lines[index:])
      data_buffer = data_buffer + self._gzip_file.read(
          self._DATA_BUFFER_SIZE)

  def _WriteAttributeContainer(self, attribute_container):
    """Writes an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.
    """
    identifier = identifiers.SerializedStreamIdentifier(
        1, self._number_of_containers)
    attribute_container.SetIdentifier(identifier)

    serialized_data = self._SerializeAttributeContainer(attribute_container)

    self._number_of_containers += 1

    self._gzip_file.write(serialized_data)
    self._gzip_file.write(b'\n')

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(error)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    # TODO: change to no longer allow event_data_identifier is None
    # after refactoring every parser to generate event data.
    event_data_identifier = event.GetEventDataIdentifier()
    if event_data_identifier:
      if not isinstance(
          event_data_identifier, identifiers.SerializedStreamIdentifier):
        raise IOError(u'Unsupported event data identifier type: {0:s}'.format(
            type(event_data_identifier)))

      event.event_data_stream_number = event_data_identifier.stream_number
      event.event_data_entry_index = event_data_identifier.entry_index

    self._WriteAttributeContainer(event)

  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(event_data)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the event tag event identifier type is not supported.
    """
    self._RaiseIfNotWritable()

    event_identifier = event_tag.GetEventIdentifier()
    if not isinstance(
        event_identifier, identifiers.SerializedStreamIdentifier):
      raise IOError(u'Unsupported event identifier type: {0:s}'.format(
          type(event_identifier)))

    event_tag.event_stream_number = event_identifier.stream_number
    event_tag.event_entry_index = event_identifier.entry_index

    self._WriteAttributeContainer(event_tag)

  def Close(self):
    """Closes the storage.

    Raises:
      IOError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError(u'Storage file already closed.')

    if self._gzip_file:
      self._gzip_file.close()
      self._gzip_file = None
    self._is_open = False

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return iter(self._GetAttributeContainerList(u'analysis_report'))

  def GetErrors(self):
    """Retrieves the errors.

    Returns:
      generator(ExtractionError): error generator.
    """
    return iter(self._GetAttributeContainerList(u'extraction_error'))

  def GetEventData(self):
    """Retrieves event data.

    Returns:
      generator(EventData): event data generator.
    """
    return iter(self._GetAttributeContainerList(u'event_data'))

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    raise NotImplementedError()

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return iter(self._GetAttributeContainerList(u'event'))

  def GetEventSources(self):
    """Retrieves the event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return iter(self._GetAttributeContainerList(u'event_source'))

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """
    for event_tag in iter(self._GetAttributeContainerList(u'event_tag')):
      event_identifier = identifiers.SerializedStreamIdentifier(
          event_tag.event_stream_number, event_tag.event_entry_index)
      event_tag.SetEventIdentifier(event_identifier)

      yield event_tag

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    event_heap = event_heaps.EventHeap()

    for event in self._GetAttributeContainerList(u'event'):
      if (time_range and (
          event.timestamp < time_range.start_timestamp or
          event.timestamp > time_range.end_timestamp)):
        continue

      event_heap.PushEvent(event)

    return iter(event_heap.PopEvents())

  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      bool: True if the storage contains analysis reports.
    """
    return len(self._GetAttributeContainerList(u'analysis_report')) > 0

  def HasErrors(self):
    """Determines if a storage contains extraction errors.

    Returns:
      bool: True if the storage contains extraction errors.
    """
    return len(self._GetAttributeContainerList(u'extraction_error')) > 0

  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """
    return len(self._GetAttributeContainerList(u'event_tags')) > 0

  # pylint: disable=arguments-differ
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

    if read_only:
      access_mode = 'rb'
    else:
      access_mode = 'wb'

    self._gzip_file = gzip.open(path, access_mode, self._COMPRESSION_LEVEL)
    if platform_specific.PlatformIsWindows():
      file_handle = self._gzip_file.fileno()
      platform_specific.DisableWindowsFileHandleInheritance(file_handle)

    if read_only:
      self._OpenRead()

    self._is_open = True
    self._read_only = read_only

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.
    """
    raise NotImplementedError()

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.
    """
    raise NotImplementedError()

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(task_start)


class GZIPStorageMergeReader(interface.FileStorageMergeReader):
  """Class that implements a gzip-based storage file reader for merging."""

  _DATA_BUFFER_SIZE = 1 * 1024 * 1024
  _MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS = 4
  _LOCKED_FILE_SLEEP_TIME = 0.5

  def __init__(self, storage_writer, path):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      path (str): path to the input file.

    Raises:
      IOError: if the input file cannot be opened.
    """
    # On Windows the file can sometimes be in use and we have to wait.
    gzip_file = None
    for attempt in range(1, self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS):
      try:
        gzip_file = gzip.open(path, 'rb')
        break
      except IOError:
        if attempt == (self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS - 1):
          raise
        time.sleep(self._LOCKED_FILE_SLEEP_TIME)

    if platform_specific.PlatformIsWindows():
      file_handle = gzip_file.fileno()
      platform_specific.DisableWindowsFileHandleInheritance(file_handle)

    super(GZIPStorageMergeReader, self).__init__(storage_writer)
    self._data_buffer = None
    self._event_data_identifier_mappings = {}
    self._gzip_file = gzip_file
    self._number_of_containers = 0
    self._path = path

  def _AddAttributeContainer(self, attribute_container):
    """Adds a single attribute container to the storage writer.

    Args:
      attribute_container (AttributeContainer): container

    Raises:
      RuntimeError: if the attribute container type is not supported.
    """
    container_type = attribute_container.CONTAINER_TYPE
    if container_type == u'event_source':
      self._storage_writer.AddEventSource(attribute_container)

    elif container_type == u'event_data':
      identifier = attribute_container.GetIdentifier()
      lookup_key = identifier.CopyToString()

      self._storage_writer.AddEventData(attribute_container)

      identifier = attribute_container.GetIdentifier()
      self._event_data_identifier_mappings[lookup_key] = identifier

    elif container_type == u'event':
      if (hasattr(attribute_container, u'event_data_stream_number') and
          hasattr(attribute_container, u'event_data_entry_index')):
        event_data_identifier = identifiers.SerializedStreamIdentifier(
            attribute_container.event_data_stream_number,
            attribute_container.event_data_entry_index)
        lookup_key = event_data_identifier.CopyToString()

        event_data_identifier = self._event_data_identifier_mappings[lookup_key]
        attribute_container.SetEventDataIdentifier(event_data_identifier)

        del attribute_container.event_data_stream_number
        del attribute_container.event_data_entry_index

      # TODO: add event identifier mappings for event tags.

      self._storage_writer.AddEvent(attribute_container)

    elif container_type == u'event_tag':
      event_identifier = identifiers.SerializedStreamIdentifier(
          attribute_container.event_stream_number,
          attribute_container.event_entry_index)
      attribute_container.SetEventIdentifier(event_identifier)

      self._storage_writer.AddEventTag(attribute_container)

    elif container_type == u'extraction_error':
      self._storage_writer.AddError(attribute_container)

    elif container_type == u'analysis_report':
      self._storage_writer.AddAnalysisReport(attribute_container)

    elif container_type not in (u'task_completion', u'task_start'):
      raise RuntimeError(u'Unsupported container type: {0:s}'.format(
          container_type))

  def MergeAttributeContainers(self, maximum_number_of_containers=0):
    """Reads attribute containers from a task storage file into the writer.

    Args:
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.

    Raises:
      OSError: if the task storage file cannot be deleted.
    """
    if not self._data_buffer:
      # Do not use gzip.readlines() here since it can consume a large amount
      # of memory.
      self._data_buffer = self._gzip_file.read(self._DATA_BUFFER_SIZE)
      self._number_of_containers = 0

    number_of_containers = 0
    while self._data_buffer:
      lines = self._data_buffer.splitlines(True)
      self._data_buffer = b''
      for index, line in enumerate(lines):
        if not line.endswith(b'\n'):
          self._data_buffer = b''.join(lines[index:])
          continue

        identifier = identifiers.SerializedStreamIdentifier(
            1, self._number_of_containers)

        attribute_container = self._DeserializeAttributeContainer(
            u'attribute_container', line)
        attribute_container.SetIdentifier(identifier)

        self._AddAttributeContainer(attribute_container)

        self._number_of_containers += 1
        number_of_containers += 1

        if (maximum_number_of_containers > 0 and
            number_of_containers >= maximum_number_of_containers):
          self._data_buffer = b''.join(lines[index+1:])
          return False

      additional_data_buffer = self._gzip_file.read(self._DATA_BUFFER_SIZE)
      self._data_buffer = b''.join([self._data_buffer, additional_data_buffer])

    self._gzip_file.close()
    self._gzip_file = None

    # On Windows the file can sometimes be in use and we have to wait.
    for attempt in range(1, self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS):
      try:
        os.remove(self._path)
        break
      except OSError:
        if attempt == (self._MAXIMUM_NUMBER_OF_LOCKED_FILE_ATTEMPTS - 1):
          raise
        time.sleep(self._LOCKED_FILE_SLEEP_TIME)

    return True


class GZIPStorageFileReader(interface.FileStorageReader):
  """Class that implements a gzip-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(GZIPStorageFileReader, self).__init__(path)
    self._storage_file = GZIPStorageFile()
    self._storage_file.Open(path=path)
