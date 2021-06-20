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

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return self._storage_file.GetAnalysisReports()

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

  def GetEventDataStreams(self):
    """Retrieves the event data streams.

    Returns:
      generator(EventDataStream): event data stream generator.
    """
    return self._storage_file.GetEventDataStreams()

  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """
    return self._storage_file.GetEventDataStreamByIdentifier(identifier)

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

  def GetExtractionWarnings(self):
    """Retrieves the extraction warnings.

    Returns:
      generator(ExtractionWarning): extraction warning generator.
    """
    return self._storage_file.GetExtractionWarnings()

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
    return self._storage_file.GetNumberOfAnalysisReports()

  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """
    return self._storage_file.GetNumberOfEventSources()

  def GetPreprocessingWarnings(self):
    """Retrieves the preprocessing warnings.

    Returns:
      generator(PreprocessingWarning): preprocessing warning generator.
    """
    return self._storage_file.GetPreprocessingWarnings()

  def GetRecoveryWarnings(self):
    """Retrieves the recovery warnings.

    Returns:
      generator(RecoveryWarning): recovery warning generator.
    """
    return self._storage_file.GetRecoveryWarnings()

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

  def HasExtractionWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """
    return self._storage_file.HasExtractionWarnings()

  def HasPreprocessingWarnings(self):
    """Determines if a store contains preprocessing warnings.

    Returns:
      bool: True if the store contains preprocessing warnings.
    """
    return self._storage_file.HasPreprocessingWarnings()

  def HasRecoveryWarnings(self):
    """Determines if a store contains recovery warnings.

    Returns:
      bool: True if the store contains recovery warnings.
    """
    return self._storage_file.HasRecoveryWarnings()

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

  def AddAnalysisReport(self, analysis_report, serialized_data=None):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
      serialized_data (Optional[bytes]): serialized form of the analysis report.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddAnalysisReport(
        analysis_report, serialized_data=serialized_data)

    self._UpdateAnalysisReportSessionCounter(analysis_report)

  def AddAnalysisWarning(self, analysis_warning, serialized_data=None):
    """Adds an analysis warning.

    Args:
      analysis_warning (AnalysisWarning): an analysis warning.
      serialized_data (Optional[bytes]): serialized form of the analysis
          warning.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddAnalysisWarning(
        analysis_warning, serialized_data=serialized_data)
    self.number_of_analysis_warnings += 1

  def AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): an event.
      serialized_data (Optional[bytes]): serialized form of the event.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEvent(event)

    self._UpdateEventParsersSessionCounter(event)

  def AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (Optional[bytes]): serialized form of the event data.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventData(event_data, serialized_data=serialized_data)

    self._UpdateEventDataParsersMappings(event_data)

  def AddEventDataStream(self, event_data_stream, serialized_data=None):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
      serialized_data (Optional[bytes]): serialized form of the event data
          stream.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventDataStream(
        event_data_stream, serialized_data=serialized_data)

  def AddEventSource(self, event_source, serialized_data=None):
    """Adds an event source.

    Args:
      event_source (EventSource): an event source.
      serialized_data (Optional[bytes]): serialized form of the event source.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventSource(
        event_source, serialized_data=serialized_data)
    self.number_of_event_sources += 1

  def AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddEventTag(event_tag, serialized_data=serialized_data)

    self._UpdateEventLabelsSessionCounter(event_tag)

  def AddExtractionWarning(self, extraction_warning, serialized_data=None):
    """Adds an extraction warning.

    Args:
      extraction_warning (ExtractionWarning): an extraction warning.
      serialized_data (Optional[bytes]): serialized form of the extraction
          warning.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddExtractionWarning(
        extraction_warning, serialized_data=serialized_data)
    self.number_of_extraction_warnings += 1

  def AddPreprocessingWarning(
      self, preprocessing_warning, serialized_data=None):
    """Adds a preprocessing warning.

    Args:
      preprocessing_warning (PreprocessingWarning): preprocessing warning.
      serialized_data (Optional[bytes]): serialized form of the preprocessing
          warning.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddPreprocessingWarning(
        preprocessing_warning, serialized_data=serialized_data)
    self.number_of_preprocessing_warnings += 1

  def AddRecoveryWarning(self, recovery_warning, serialized_data=None):
    """Adds a recovery warning.

    Args:
      recovery_warning (RecoveryWarning): an recovery warning.
      serialized_data (Optional[bytes]): serialized form of the recovery
          warning.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddRecoveryWarning(
        recovery_warning, serialized_data=serialized_data)
    self.number_of_recovery_warnings += 1

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

  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """
    return self._storage_file.GetEventDataStreamByIdentifier(identifier)

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

    self._first_written_event_source_index = (
        self._storage_file.GetNumberOfEventSources())
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
