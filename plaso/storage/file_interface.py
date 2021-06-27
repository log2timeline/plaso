# -*- coding: utf-8 -*-
"""Storage interface classes for file-based stores."""

import abc
import collections

from plaso.lib import definitions
from plaso.serializer import json_serializer
from plaso.storage import interface


class BaseStorageFile(interface.BaseStore):
  """Interface for file-based stores."""

  # pylint: disable=abstract-method

  def __init__(self):
    """Initializes a file-based store."""
    super(BaseStorageFile, self).__init__()
    self._attribute_container_sequence_numbers = collections.Counter()
    self._is_open = False
    self._read_only = True
    self._serializer = json_serializer.JSONAttributeContainerSerializer

  def _GetAttributeContainerNextSequenceNumber(self, container_type):
    """Retrieves the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: next sequence number.
    """
    self._attribute_container_sequence_numbers[container_type] += 1
    return self._attribute_container_sequence_numbers[container_type]

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

  def _SetAttributeContainerNextSequenceNumber(
      self, container_type, next_sequence_number):
    """Sets the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.
      next_sequence_number (int): next sequence number.
    """
    self._attribute_container_sequence_numbers[
        container_type] = next_sequence_number


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

  def Close(self):
    """Closes the storage reader."""
    if self._storage_file:
      self._storage_file.Close()
      self._storage_file = None

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    return self._storage_file.GetAttributeContainerByIdentifier(
        container_type, identifier)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    return self._storage_file.GetAttributeContainers(container_type)

  def GetFormatVersion(self):
    """Retrieves the format version of the underlying storage file.

    Returns:
      int: the format version, or None if not available.
    """
    if self._storage_file:
      return self._storage_file.format_version

    return None

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._storage_file.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """
    return self._storage_file.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

  def GetSerializationFormat(self):
    """Retrieves the serialization format of the underlying storage file.

    Returns:
      str: the serialization format, or None if not available.
    """
    if self._storage_file:
      return self._storage_file.serialization_format

    return None

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

  def GetStorageType(self):
    """Retrieves the storage type of the underlying storage file.

    Returns:
      str: the storage type, or None if not available.
    """
    if self._storage_file:
      return self._storage_file.storage_type

    return None

  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    return self._storage_file.HasAttributeContainers(container_type)

  # TODO: remove, this method is kept for backwards compatibility reasons.
  def ReadSystemConfiguration(self, knowledge_base):
    """Reads system configuration information.

    The system configuration contains information about various system specific
    configuration data, for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the system configuration.
    """
    self._storage_file.ReadSystemConfiguration(knowledge_base)

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
    self._output_file = output_file
    self._storage_file = None

  @abc.abstractmethod
  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      BaseStorageFile: storage file.
    """

  def _RaiseIfNotWritable(self):
    """Raises if the storage writer is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to write to closed storage writer.')

  def AddAttributeContainer(self, container):
    """Adds an attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddAttributeContainer(container)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_REPORT:
      self._UpdateAnalysisReportSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_WARNING:
      self.number_of_analysis_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      self._UpdateEventParsersSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._UpdateEventDataParsersMappings(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_SOURCE:
      self.number_of_event_sources += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG:
      self._UpdateEventLabelsSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EXTRACTION_WARNING:
      self.number_of_extraction_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_PREPROCESSING_WARNING:
      self.number_of_preprocessing_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_RECOVERY_WARNING:
      self.number_of_recovery_warnings += 1

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): an event.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddAttributeContainer(event)

    self._UpdateEventParsersSessionCounter(event)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    # TODO: refactor to use AddOrUpdateAttributeContainer
    self._storage_file.AddEventTag(event_tag)

    self._UpdateEventLabelsSessionCounter(event_tag)

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.Close()
    self._storage_file = None

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    return self._storage_file.GetAttributeContainerByIdentifier(
        container_type, identifier)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    return self._storage_file.GetAttributeContainers(container_type)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    return self._storage_file.GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT)

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """
    return self._storage_file.GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_TAG, identifier)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTag): event tag generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    return self._storage_file.GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_TAG)

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

    event_source = self._storage_file.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE,
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

    event_source = self._storage_file.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE, self._written_event_source_index)
    if event_source:
      self._written_event_source_index += 1
    return event_source

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

  def Open(self, **unused_kwargs):
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

    number_of_event_sources = self._storage_file.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)
    self._first_written_event_source_index = number_of_event_sources
    self._written_event_source_index = self._first_written_event_source_index

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

    # TODO: move self._session out of the StorageFileWriter?
    self._session.aborted = aborted
    session_completion = self._session.CreateSessionCompletion()
    self._storage_file.WriteSessionCompletion(session_completion)

  def WriteSessionConfiguration(self):
    """Writes session configuration information.

    Raises:
      IOError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
      OSError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session configuration not supported by storage type.')

    # TODO: move self._session out of the StorageFileWriter?
    session_configuration = self._session.CreateSessionConfiguration()
    self._storage_file.WriteSessionConfiguration(session_configuration)

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

    # TODO: move self._session out of the StorageFileWriter?
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
