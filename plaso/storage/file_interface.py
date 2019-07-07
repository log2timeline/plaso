# -*- coding: utf-8 -*-
"""Storage interface classes for file-backed stores."""

from __future__ import unicode_literals

import abc
import os
import shutil
import tempfile

from plaso.lib import definitions
from plaso.serializer import json_serializer
from plaso.storage import interface


class SerializedAttributeContainerList(object):
  """Serialized attribute container list.

  The list is unsorted and pops attribute containers in the same order as
  pushed to preserve order.

  The GetAttributeContainerByIndex method should be used to read attribute
  containers from the list while it being filled.

  Attributes:
    data_size (int): total data size of the serialized attribute containers
        on the list.
    next_sequence_number (int): next attribute container sequence number.
  """

  def __init__(self):
    """Initializes a serialized attribute container list."""
    super(SerializedAttributeContainerList, self).__init__()
    self._list = []
    self.data_size = 0
    self.next_sequence_number = 0

  @property
  def number_of_attribute_containers(self):
    """int: number of serialized attribute containers on the list."""
    return len(self._list)

  def Empty(self):
    """Empties the list."""
    self._list = []
    self.data_size = 0

  def GetAttributeContainerByIndex(self, index):
    """Retrieves a specific serialized attribute container from the list.

    Args:
      index (int): attribute container index.

    Returns:
      bytes: serialized attribute container data or None if not available.

    Raises:
      IndexError: if the index is less than zero.
    """
    if index < 0:
      raise IndexError(
          'Unsupported negative index value: {0:d}.'.format(index))

    if index < len(self._list):
      return self._list[index]

    return None

  def PopAttributeContainer(self):
    """Pops a serialized attribute container from the list.

    Returns:
      bytes: serialized attribute container data or None if the list is empty.
    """
    try:
      serialized_data = self._list.pop(0)
      self.data_size -= len(serialized_data)
      return serialized_data

    except IndexError:
      return None

  def PushAttributeContainer(self, serialized_data):
    """Pushes a serialized attribute container onto the list.

    Args:
      serialized_data (bytes): serialized attribute container data.
    """
    self._list.append(serialized_data)
    self.data_size += len(serialized_data)
    self.next_sequence_number += 1


class BaseStorageFile(interface.BaseStore):
  """Interface for file-based stores."""

  # pylint: disable=abstract-method

  def __init__(self):
    """Initializes a file-based store."""
    super(BaseStorageFile, self).__init__()
    self._is_open = False
    self._read_only = True
    self._serialized_attribute_containers = {}
    self._serializer = json_serializer.JSONAttributeContainerSerializer

  def _GetNumberOfSerializedAttributeContainers(self, container_type):
    """Retrieves the number of serialized attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: number of serialized attribute containers.
    """
    container_list = self._GetSerializedAttributeContainerList(container_type)
    return container_list.number_of_attribute_containers

  def _GetSerializedAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific serialized attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      bytes: serialized attribute container data or None if not available.
    """
    container_list = self._GetSerializedAttributeContainerList(container_type)
    return container_list.GetAttributeContainerByIndex(index)

  def _GetSerializedAttributeContainerList(self, container_type):
    """Retrieves a serialized attribute container list.

    Args:
      container_type (str): attribute container type.

    Returns:
      SerializedAttributeContainerList: serialized attribute container list.
    """
    container_list = self._serialized_attribute_containers.get(
        container_type, None)
    if not container_list:
      container_list = SerializedAttributeContainerList()
      self._serialized_attribute_containers[container_type] = container_list

    return container_list

  def _SerializeAttributeContainer(self, attribute_container):
    """Serializes an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      bytes: serialized attribute container.

    Raises:
      IOError: if the attribute container cannot be serialized.
      OSError: if the attribute container cannot be serialized.
    """
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(
          attribute_container.CONTAINER_TYPE)

    try:
      attribute_container_data = self._serializer.WriteSerialized(
          attribute_container)
      if not attribute_container_data:
        raise IOError(
            'Unable to serialize attribute container: {0:s}.'.format(
                attribute_container.CONTAINER_TYPE))

      attribute_container_data = attribute_container_data.encode('utf-8')

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(
            attribute_container.CONTAINER_TYPE)

    return attribute_container_data

  def _RaiseIfNotReadable(self):
    """Raises if the storage file is not readable.

     Raises:
      IOError: when the storage file is closed.
      OSError: when the storage file is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage file.')

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage file.')

    if self._read_only:
      raise IOError('Unable to write to read-only storage file.')


class StorageFileMergeReader(interface.StorageMergeReader):
  """Storage reader interface for merging file-based stores."""

  # pylint: disable=abstract-method

  def __init__(self, storage_writer):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    super(StorageFileMergeReader, self).__init__(storage_writer)
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None


class StorageFileReader(interface.StorageReader):
  """File-based storage reader interface."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(StorageFileReader, self).__init__()
    self._path = path
    self._storage_file = None

  def GetFormatVersion(self):
    """Retrieves the format version of the underlying storage file.

    Returns:
      int: the format version, or None if not available.
    """
    if self._storage_file:
      return self._storage_file.format_version

    return None

  def GetSerializationFormat(self):
    """Retrieves the serialization format of the underlying storage file.

    Returns:
      str: the serialization format, or None if not available.
    """
    if self._storage_file:
      return self._storage_file.serialization_format

    return None

  def GetStorageType(self):
    """Retrieves the storage type of the underlying storage file.

    Returns:
      str: the storage type, or None if not available.
    """
    if self._storage_file:
      return self._storage_file.storage_type

    return None

  def Close(self):
    """Closes the storage reader."""
    if self._storage_file:
      self._storage_file.Close()
      self._storage_file = None

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return self._storage_file.GetAnalysisReports()

  def GetWarnings(self):
    """Retrieves the warnings.

    Returns:
      generator(ExtractionWarning): warning generator.
    """
    return self._storage_file.GetWarnings()

  def GetEventData(self):
    """Retrieves the event data.

    Returns:
      generator(EventData): event data generator.
    """
    return self._storage_file.GetEventData()

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    return self._storage_file.GetEventDataByIdentifier(identifier)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return self._storage_file.GetEvents()

  def GetEventSources(self):
    """Retrieves the event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return self._storage_file.GetEventSources()

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """
    return self._storage_file.GetEventTagByIdentifier(identifier)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTag): event tag generator.
    """
    return self._storage_file.GetEventTags()

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._storage_file.GetNumberOfAnalysisReports()

  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """
    return self._storage_file.GetNumberOfEventSources()

  def GetSessions(self):
    """Retrieves the sessions.

    Returns:
      generator(Session): session generator.
    """
    return self._storage_file.GetSessions()

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    return self._storage_file.GetSortedEvents(time_range=time_range)

  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """
    return self._storage_file.HasAnalysisReports()

  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """
    return self._storage_file.HasEventTags()

  def HasWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """
    return self._storage_file.HasWarnings()

  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
    """
    self._storage_file.ReadPreprocessingInformation(knowledge_base)

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._storage_file.SetSerializersProfiler(serializers_profiler)

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_file.SetStorageProfiler(storage_profiler)


class StorageFileWriter(interface.StorageWriter):
  """Defines an interface for a file-backed storage writer."""

  def __init__(
      self, session, output_file,
      storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      output_file (str): path to the output file.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(StorageFileWriter, self).__init__(
        session, storage_type=storage_type, task=task)
    self._merge_task_storage_path = ''
    self._output_file = output_file
    self._processed_task_storage_path = ''
    self._storage_file = None
    self._task_storage_path = None

  @abc.abstractmethod
  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      BaseStorageFile: storage file.
    """

  @abc.abstractmethod
  def _CreateTaskStorageMergeReader(self, task):
    """Creates a task storage merge reader.

    Args:
      task (Task): task.

    Returns:
      StorageMergeReader: storage merge reader.
    """

  @abc.abstractmethod
  def _CreateTaskStorageWriter(self, task):
    """Creates a task storage writer.

    Args:
      task (Task): task.

    Returns:
      StorageWriter: storage writer.
    """

  def _GetMergeTaskStorageFilePath(self, task):
    """Retrieves the path of a task storage file in the merge directory.

    Args:
      task (Task): task.

    Returns:
      str: path of a task storage file file in the merge directory.
    """
    filename = '{0:s}.plaso'.format(task.identifier)
    return os.path.join(self._merge_task_storage_path, filename)

  def _GetProcessedStorageFilePath(self, task):
    """Retrieves the path of a task storage file in the processed directory.

    Args:
      task (Task): task.

    Returns:
      str: path of a task storage file in the processed directory.
    """
    filename = '{0:s}.plaso'.format(task.identifier)
    return os.path.join(self._processed_task_storage_path, filename)

  def _GetTaskStorageFilePath(self, task):
    """Retrieves the path of a task storage file in the temporary directory.

    Args:
      task (Task): task.

    Returns:
      str: path of a task storage file in the temporary directory.
    """
    filename = '{0:s}.plaso'.format(task.identifier)
    return os.path.join(self._task_storage_path, filename)

  def _UpdateCounters(self, event):
    """Updates the counters.

    Args:
      event (EventObject): event.
    """
    self._session.parsers_counter['total'] += 1

    # Here we want the name of the parser or plugin not the parser chain.
    parser_name = getattr(event, 'parser', '')
    _, _, parser_name = parser_name.rpartition('/')
    if not parser_name:
      parser_name = 'N/A'
    self._session.parsers_counter[parser_name] += 1

  def _RaiseIfNotWritable(self):
    """Raises if the storage writer is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to write to closed storage writer.')

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddAnalysisReport(analysis_report)

    report_identifier = analysis_report.plugin_name
    self._session.analysis_reports_counter['total'] += 1
    self._session.analysis_reports_counter[report_identifier] += 1
    self.number_of_analysis_reports += 1

  def AddWarning(self, warning):
    """Adds an warning.

    Args:
      warning (ExtractionWarning): an extraction warning.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddWarning(warning)
    self.number_of_warnings += 1

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): an event.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEvent(event)
    self.number_of_events += 1

    self._UpdateCounters(event)

  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventData(event_data)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): an event source.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventSource(event_source)
    self.number_of_event_sources += 1

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventTag(event_tag)

    self._session.event_labels_counter['total'] += 1
    for label in event_tag.labels:
      self._session.event_labels_counter[label] += 1
    self.number_of_event_tags += 1

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.Close()
    self._storage_file = None

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    return self._storage_file.GetEventDataByIdentifier(identifier)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    return self._storage_file.GetEvents()

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """
    return self._storage_file.GetEventTagByIdentifier(identifier)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTag): event tag generator.
    """
    return self._storage_file.GetEventTags()

  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

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
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

    event_source = self._storage_file.GetEventSourceByIndex(
        self._written_event_source_index)
    if event_source:
      self._written_event_source_index += 1
    return event_source

  def GetProcessedTaskIdentifiers(self):
    """Identifiers for tasks which have been processed.

    Returns:
      list[str]: task identifiers that are processed.

    Raises:
      IOError: if the storage type is not supported or
          if the temporary path for the task storage does not exist.
      OSError: if the storage type is not supported or
          if the temporary path for the task storage does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if not self._processed_task_storage_path:
      raise IOError('Missing processed task storage path.')

    return [
        path.replace('.plaso', '')
        for path in os.listdir(self._processed_task_storage_path)]

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

    return self._storage_file.GetSortedEvents(time_range=time_range)

  def FinalizeTaskStorage(self, task):
    """Finalizes a processed task storage.

    Moves the task storage file from its temporary directory to the processed
    directory.

    Args:
      task (Task): task.

    Raises:
      IOError: if the storage type or format is not supported or
          if the storage file cannot be renamed.
      OSError: if the storage type or format is not supported or
          if the storage file cannot be renamed.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if not task.storage_format in definitions.STORAGE_FORMATS:
      raise IOError('Unsupported storage format')

    if task.storage_format == definitions.STORAGE_FORMAT_SQLITE:
      storage_file_path = self._GetTaskStorageFilePath(task)
      processed_storage_file_path = self._GetProcessedStorageFilePath(task)

      try:
        os.rename(storage_file_path, processed_storage_file_path)
      except OSError as exception:
        raise IOError((
            'Unable to rename task storage file: {0:s} with error: '
            '{1!s}').format(storage_file_path, exception))

  def Open(self):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._storage_file:
      raise IOError('Storage writer already opened.')

    self._storage_file = self._CreateStorageFile()

    if self._serializers_profiler:
      self._storage_file.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._storage_file.SetStorageProfiler(self._storage_profiler)

    self._storage_file.Open(path=self._output_file, read_only=False)

    self._first_written_event_source_index = (
        self._storage_file.GetNumberOfEventSources())
    self._written_event_source_index = self._first_written_event_source_index

  def PrepareMergeTaskStorage(self, task):
    """Prepares a task storage for merging.

    Moves the task storage file from the processed directory to the merge
    directory.

    Args:
      task (Task): task.

    Raises:
      IOError: if the storage type is not supported or
          if the storage file cannot be renamed.
      OSError: if the storage type is not supported or
          if the storage file cannot be renamed.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    merge_storage_file_path = self._GetMergeTaskStorageFilePath(task)
    processed_storage_file_path = self._GetProcessedStorageFilePath(task)

    task.storage_file_size = os.path.getsize(processed_storage_file_path)

    try:
      os.rename(processed_storage_file_path, merge_storage_file_path)
    except OSError as exception:
      raise IOError((
          'Unable to rename task storage file: {0:s} with error: '
          '{1!s}').format(processed_storage_file_path, exception))

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
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

    self._storage_file.ReadPreprocessingInformation(knowledge_base)

  def RemoveProcessedTaskStorage(self, task):
    """Removes a processed task storage.

    Args:
      task (Task): task.

    Raises:
      IOError: if the storage type or format is not supported or
          if the storage file cannot be removed.
      OSError: if the storage type or format is not supported or
          if the storage file cannot be removed.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if task.storage_format != definitions.STORAGE_FORMAT_SQLITE:
      raise IOError('Unsupported storage format.')

    processed_storage_file_path = self._GetProcessedStorageFilePath(task)

    try:
      os.remove(processed_storage_file_path)
    except OSError as exception:
      raise IOError((
          'Unable to remove task storage file: {0:s} with error: '
          '{1!s}').format(processed_storage_file_path, exception))

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler
    if self._storage_file:
      self._storage_file.SetSerializersProfiler(serializers_profiler)

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_profiler = storage_profiler
    if self._storage_file:
      self._storage_file.SetStorageProfiler(storage_profiler)

  def StartMergeTaskStorage(self, task):
    """Starts a merge of a task store with the session storage.

    Args:
      task (Task): task.

    Returns:
      StorageMergeReader: storage merge reader of the task storage.

    Raises:
      IOError: if the storage file cannot be opened or
          if the storage type is not supported or
          if the temporary path for the task storage does not exist or
          if the temporary path for the task storage doe not refers to a file.
      OSError: if the storage file cannot be opened or
          if the storage type is not supported or
          if the temporary path for the task storage does not exist or
          if the temporary path for the task storage doe not refers to a file.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if not self._merge_task_storage_path:
      raise IOError('Missing merge task storage path.')

    merge_storage_file_path = self._GetMergeTaskStorageFilePath(task)

    if (task.storage_format == definitions.STORAGE_FORMAT_SQLITE and not
        os.path.isfile(merge_storage_file_path)):
      raise IOError('Merge task storage path is not a file.')

    return self._CreateTaskStorageMergeReader(task)

  def StartTaskStorage(self):
    """Creates a temporary path for the task storage.

    Raises:
      IOError: if the storage type is not supported or
          if the temporary path for the task storage already exists.
      OSError: if the storage type is not supported or
          if the temporary path for the task storage already exists.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if self._task_storage_path:
      raise IOError('Task storage path already exists.')

    output_directory = os.path.dirname(self._output_file)
    self._task_storage_path = tempfile.mkdtemp(dir=output_directory)

    self._merge_task_storage_path = os.path.join(
        self._task_storage_path, 'merge')
    os.mkdir(self._merge_task_storage_path)

    self._processed_task_storage_path = os.path.join(
        self._task_storage_path, 'processed')
    os.mkdir(self._processed_task_storage_path)

  def StopTaskStorage(self, abort=False):
    """Removes the temporary path for the task storage.

    The results of tasks will be lost on abort.

    Args:
      abort (bool): True to indicate the stop is issued on abort.

    Raises:
      IOError: if the storage type is not supported.
      OSError: if the storage type is not supported.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if os.path.isdir(self._merge_task_storage_path):
      if abort:
        shutil.rmtree(self._merge_task_storage_path)
      else:
        os.rmdir(self._merge_task_storage_path)

    if os.path.isdir(self._processed_task_storage_path):
      if abort:
        shutil.rmtree(self._processed_task_storage_path)
      else:
        os.rmdir(self._processed_task_storage_path)

    if os.path.isdir(self._task_storage_path):
      if abort:
        shutil.rmtree(self._task_storage_path)
      else:
        os.rmdir(self._task_storage_path)

    self._merge_task_storage_path = None
    self._processed_task_storage_path = None
    self._task_storage_path = None

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocessing
          information or when the storage writer is closed.
      OSError: if the storage type does not support writing preprocessing
          information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Preprocessing information not supported by storage type.')

    self._storage_file.WritePreprocessingInformation(knowledge_base)

  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    self._session.aborted = aborted
    session_completion = self._session.CreateSessionCompletion()
    self._storage_file.WriteSessionCompletion(session_completion)

  def WriteSessionStart(self):
    """Writes session start information.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    session_start = self._session.CreateSessionStart()
    self._storage_file.WriteSessionStart(session_start)

  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Unsupported storage type.')

    self._task.aborted = aborted
    task_completion = self._task.CreateTaskCompletion()
    self._storage_file.WriteTaskCompletion(task_completion)

  def WriteTaskStart(self):
    """Writes task start information.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Unsupported storage type.')

    task_start = self._task.CreateTaskStart()
    self._storage_file.WriteTaskStart(task_start)
