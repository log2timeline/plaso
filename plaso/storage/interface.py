# -*- coding: utf-8 -*-
"""The storage interface classes."""

import abc

from plaso.containers import artifacts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.serializer import json_serializer


class BaseStore(object):
  """Storage interface.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_ANALYSIS_WARNING = warnings.AnalysisWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_PREPROCESSING_WARNING = (
      warnings.PreprocessingWarning.CONTAINER_TYPE)
  _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_COMPLETION = sessions.SessionCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_CONFIGURATION = (
      sessions.SessionConfiguration.CONTAINER_TYPE)
  _CONTAINER_TYPE_SESSION_START = sessions.SessionStart.CONTAINER_TYPE
  _CONTAINER_TYPE_SYSTEM_CONFIGURATION = (
      artifacts.SystemConfigurationArtifact.CONTAINER_TYPE)
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_ANALYSIS_REPORT,
      _CONTAINER_TYPE_ANALYSIS_WARNING,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT_DATA_STREAM,
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_PREPROCESSING_WARNING,
      _CONTAINER_TYPE_RECOVERY_WARNING,
      _CONTAINER_TYPE_SESSION_COMPLETION,
      _CONTAINER_TYPE_SESSION_CONFIGURATION,
      _CONTAINER_TYPE_SESSION_START,
      _CONTAINER_TYPE_SYSTEM_CONFIGURATION,
      _CONTAINER_TYPE_TASK_COMPLETION,
      _CONTAINER_TYPE_TASK_START)

  # Container types that only should be used in a session store.
  _SESSION_STORE_ONLY_CONTAINER_TYPES = (
      _CONTAINER_TYPE_SESSION_COMPLETION,
      _CONTAINER_TYPE_SESSION_START,
      _CONTAINER_TYPE_SYSTEM_CONFIGURATION)

  # Container types that only should be used in a task store.
  _TASK_STORE_ONLY_CONTAINER_TYPES = (
      _CONTAINER_TYPE_TASK_COMPLETION,
      _CONTAINER_TYPE_TASK_START)

  def __init__(self):
    """Initializes a store."""
    super(BaseStore, self).__init__()
    self._last_session = 0
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None
    self._storage_profiler = None
    self.format_version = None
    self.serialization_format = None
    self.storage_type = None

  @abc.abstractmethod
  def _AddAttributeContainer(
      self, container_type, container, serialized_data=None):
    """Adds an attribute container.

    Args:
      container_type (str): attribute container type.
      container (AttributeContainer): attribute container.
      serialized_data (Optional[bytes]): serialized form of the container.
    """

  @abc.abstractmethod
  def _GetAttributeContainers(self, container_type):
    """Yields attribute containers

    Args:
      container_type (str): container type attribute of the container being
        added.

    Yields:
      AttributeContainer: attribute container.
    """

  @abc.abstractmethod
  def _GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves the container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      OSError: if an invalid identifier is provided.
      IOError: if an invalid identifier is provided.
    """

  @abc.abstractmethod
  def _RaiseIfNotWritable(self):
    """Raises if the store is not writable.

     Raises:
       OSError: if the store cannot be written to.
       IOError: if the store cannot be written to.
    """

  @abc.abstractmethod
  def _RaiseIfNotReadable(self):
    """Raises if the store is not readable.

     Raises:
       OSError: if the store cannot be read from.
       IOError: if the store cannot be read from.
    """

  @abc.abstractmethod
  def _HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """

  @abc.abstractmethod
  def _GetNumberOfAttributeContainers(self, container_type):
    """Determines the number of containers of a type in the store.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers in the store of the specified type.
    """

  @abc.abstractmethod
  def _WriteAttributeContainer(self, attribute_container):
    """Writes an attribute container to the store.

    Args:
      attribute_container (AttributeContainer): attribute container.
    """

  def AddAnalysisReport(self, analysis_report, serialized_data=None):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
      serialized_data (Optional[bytes]): serialized form of the analysis report.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_ANALYSIS_REPORT, analysis_report,
        serialized_data=serialized_data)

  def AddAnalysisWarning(self, analysis_warning, serialized_data=None):
    """Adds an analysis warning.

    Args:
      analysis_warning (AnalysisWarning): analysis warning.
      serialized_data (Optional[bytes]): serialized form of the analysis
          warning.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_ANALYSIS_WARNING, analysis_warning,
        serialized_data=serialized_data)

  def AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT, event, serialized_data=serialized_data)

  def AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (Optional[bytes]): serialized form of the event data.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT_DATA, event_data,
        serialized_data=serialized_data)

  def AddEventDataStream(self, event_data_stream, serialized_data=None):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
      serialized_data (Optional[bytes]): serialized form of the event data
          stream.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT_DATA_STREAM, event_data_stream,
        serialized_data=serialized_data)

  def AddEventSource(self, event_source, serialized_data=None):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
      serialized_data (Optional[bytes]): serialized form of the event source.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT_SOURCE, event_source,
        serialized_data=serialized_data)

  def AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT_TAG, event_tag,
        serialized_data=serialized_data)

  def AddExtractionWarning(self, extraction_warning, serialized_data=None):
    """Adds an extraction warning.

    Args:
      extraction_warning (ExtractionWarning): extraction warning.
      serialized_data (Optional[bytes]): serialized form of the extraction
          warning.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EXTRACTION_WARNING, extraction_warning,
        serialized_data=serialized_data)

  def AddPreprocessingWarning(
      self, preprocessing_warning, serialized_data=None):
    """Adds a preprocessing warning.

    Args:
      preprocessing_warning (PreprocessingWarning): preprocessing warning.
      serialized_data (Optional[bytes]): serialized form of the preprocessing
          warning.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_PREPROCESSING_WARNING, preprocessing_warning,
        serialized_data=serialized_data)

  def AddRecoveryWarning(self, recovery_warning, serialized_data=None):
    """Adds a recovery warning.

    Args:
      recovery_warning (RecoveryWarning): recovery warning.
      serialized_data (Optional[bytes]): serialized form of the recovery
          warning.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_RECOVERY_WARNING, recovery_warning,
        serialized_data=serialized_data)

  @abc.abstractmethod
  def Close(self):
    """Closes the store."""

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetAnalysisWarnings(self):
    """Retrieves the analysis warnings.

    Returns:
      generator(AnalysisWarning): analysis warning generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_WARNING)

  def GetEventData(self):
    """Retrieves the event data.

    Returns:
      generator(EventData): event data generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT_DATA)

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    return self._GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_DATA, identifier)

  def GetEventDataStreams(self):
    """Retrieves the event data streams.

    Returns:
      generator(EventDataStream): event data stream generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT_DATA_STREAM)

  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """
    return self._GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_DATA_STREAM, identifier)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(Event): event generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT)

  def GetEventSources(self):
    """Retrieves the event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT_SOURCE)

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.

    Raises:
      OSError: if an invalid identifier is provided.
      IOError: if an invalid identifier is provided.
    """
    return self._GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_TAG, identifier)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTag): event tag generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT_TAG)

  def GetExtractionWarnings(self):
    """Retrieves the extraction warnings.

    Returns:
      generator(ExtractionWarning): extraction warning generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EXTRACTION_WARNING)

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

    Returns:
      int: number of event sources.
    """
    return self._GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

  def GetPreprocessingWarnings(self):
    """Retrieves the preprocessing warnings.

    Returns:
      generator(PreprocessingWarning): preprocessing warning generator.
    """
    return self._GetAttributeContainers(
        self._CONTAINER_TYPE_PREPROCESSING_WARNING)

  def GetRecoveryWarnings(self):
    """Retrieves the recovery warnings.

    Returns:
      generator(RecoveryWarning): recovery warning generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_RECOVERY_WARNING)

  def GetSessions(self):
    """Retrieves the sessions.

    Yields:
      Session: session attribute container.

    Raises:
      IOError: if there is a mismatch in session identifiers between the
          session start and completion attribute containers.
      OSError: if there is a mismatch in session identifiers between the
          session start and completion attribute containers.
    """
    session_start_generator = self._GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)
    session_completion_generator = self._GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    if self._HasAttributeContainers(self._CONTAINER_TYPE_SESSION_CONFIGURATION):
      session_configuration_generator = self._GetAttributeContainers(
          self._CONTAINER_TYPE_SESSION_CONFIGURATION)
    else:
      session_configuration_generator = None

    for session_index in range(1, self._last_session + 1):
      try:
        session_start = next(session_start_generator)
      except StopIteration:
        raise IOError('Missing session start: {0:d}'.format(session_index))

      try:
        session_completion = next(session_completion_generator)
      except StopIteration:
        pass

      session_configuration = None
      if session_configuration_generator:
        try:
          session_configuration = next(session_configuration_generator)
        except StopIteration:
          raise IOError('Missing session configuration: {0:d}'.format(
              session_index))

      session = sessions.Session()
      session.CopyAttributesFromSessionStart(session_start)

      if session_configuration:
        try:
          session.CopyAttributesFromSessionConfiguration(session_configuration)
        except ValueError:
          raise IOError((
              'Session identifier mismatch for session configuration: '
              '{0:d}').format(session_index))

      if session_completion:
        try:
          session.CopyAttributesFromSessionCompletion(session_completion)
        except ValueError:
          raise IOError((
              'Session identifier mismatch for session completion: '
              '{0:d}').format(session_index))

      yield session

  @abc.abstractmethod
  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the store including those pending
    being flushed (written) to the store.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      EventObject: event.
    """

  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def HasAnalysisWarnings(self):
    """Determines if a store contains analysis warnings.

    Returns:
      bool: True if the store contains analysis warnings.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_WARNING)

  def HasExtractionWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_EXTRACTION_WARNING)

  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_EVENT_TAG)

  def HasPreprocessingWarnings(self):
    """Determines if a store contains preprocessing warnings.

    Returns:
      bool: True if the store contains preprocessing warnings.
    """
    return self._HasAttributeContainers(
        self._CONTAINER_TYPE_PREPROCESSING_WARNING)

  def HasRecoveryWarnings(self):
    """Determines if a store contains recovery warnings.

    Returns:
      bool: True if the store contains recovery warnings.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_RECOVERY_WARNING)

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage."""

  # TODO: remove, this method is kept for backwards compatibility reasons.
  def ReadSystemConfiguration(self, knowledge_base):
    """Reads system configuration information.

    The system configuration contains information about various system specific
    configuration data, for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the system configuration.
    """
    # Backwards compatibility for older session storage files that do not
    # store system configuration as part of the session configuration.
    if self._HasAttributeContainers(self._CONTAINER_TYPE_SYSTEM_CONFIGURATION):
      generator = self._GetAttributeContainers(
          self._CONTAINER_TYPE_SYSTEM_CONFIGURATION)
      for system_configuration in generator:
        knowledge_base.ReadSystemConfigurationArtifact(system_configuration)

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_profiler = storage_profiler

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.

    Raises:
      IOError: if the storage type does not support writing a session
          completion or the storage file is closed or read-only.
      OSError: if the storage type does not support writing a session
          completion or the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session completion not supported by storage type.')

    self._WriteAttributeContainer(session_completion)

  def WriteSessionConfiguration(self, session_configuration):
    """Writes session configuration information.

    Args:
      session_configuration (SessionConfiguration): session configuration
          information.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if not self._HasAttributeContainers(
        self._CONTAINER_TYPE_SYSTEM_CONFIGURATION):
      self._WriteAttributeContainer(session_configuration)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.

    Raises:
      IOError: if the storage type does not support writing a session
          start or the storage file is closed or read-only.
      OSError: if the storage type does not support writing a session
          start or the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session start not supported by storage type.')

    self._WriteAttributeContainer(session_start)

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: if the storage type does not support writing a task
          completion or the storage file is closed or read-only.
      OSError: if the storage type does not support writing a task
          completion or the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Task start not supported by storage type.')

    self._WriteAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      IOError: if the storage type does not support writing a task
          start or the storage file is closed or read-only.
      OSError: if the storage type does not support writing a task
          start or the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Task completion not supported by storage type.')

    self._WriteAttributeContainer(task_start)

  def _DeserializeAttributeContainer(self, container_type, serialized_data):
    """Deserializes an attribute container.

    Args:
      container_type (str): attribute container type.
      serialized_data (bytes): serialized attribute container data.

    Returns:
      AttributeContainer: attribute container or None.

    Raises:
      IOError: if the serialized data cannot be decoded.
      OSError: if the serialized data cannot be decoded.
    """
    if not serialized_data:
      return None

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(container_type)

    try:
      serialized_string = serialized_data.decode('utf-8')
      attribute_container = self._serializer.ReadSerialized(serialized_string)

    except UnicodeDecodeError as exception:
      raise IOError('Unable to decode serialized data: {0!s}'.format(exception))

    except (TypeError, ValueError) as exception:
      # TODO: consider re-reading attribute container with error correction.
      raise IOError('Unable to read serialized data: {0!s}'.format(exception))

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(container_type)

    return attribute_container

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

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(
            attribute_container.CONTAINER_TYPE)

    return attribute_container_data


class StorageMergeReader(object):
  """Storage reader interface for merging."""

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_ANALYSIS_WARNING = warnings.AnalysisWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  # Some container types reference other container types, such as event
  # referencing event_data. Container types in this tuple must be ordered after
  # all the container types they reference.
  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_DATA_STREAM,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_RECOVERY_WARNING,
      _CONTAINER_TYPE_ANALYSIS_REPORT,
      _CONTAINER_TYPE_ANALYSIS_WARNING)

  _ADD_CONTAINER_TYPE_METHODS = {
      _CONTAINER_TYPE_ANALYSIS_REPORT: '_AddAnalysisReport',
      _CONTAINER_TYPE_ANALYSIS_WARNING: '_AddAnalysisWarning',
      _CONTAINER_TYPE_EVENT: '_AddEvent',
      _CONTAINER_TYPE_EVENT_DATA: '_AddEventData',
      _CONTAINER_TYPE_EVENT_DATA_STREAM: '_AddEventDataStream',
      _CONTAINER_TYPE_EVENT_SOURCE: '_AddEventSource',
      _CONTAINER_TYPE_EVENT_TAG: '_AddEventTag',
      _CONTAINER_TYPE_EXTRACTION_WARNING: '_AddExtractionWarning',
      _CONTAINER_TYPE_RECOVERY_WARNING: '_AddRecoveryWarning'}

  def __init__(self, storage_writer):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    super(StorageMergeReader, self).__init__()
    self._storage_profiler = None
    self._storage_writer = storage_writer
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None

  def _AddAnalysisReport(self, analysis_report, serialized_data=None):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
      serialized_data (Optional[bytes]): serialized form of the analysis report.
    """
    self._storage_writer.AddAnalysisReport(
        analysis_report, serialized_data=serialized_data)

  def _AddAnalysisWarning(self, analysis_warning, serialized_data=None):
    """Adds an analysis warning.

    Args:
      analysis_warning (AnalysisWarning): analysis warning.
      serialized_data (Optional[bytes]): serialized form of the warning.
    """
    self._storage_writer.AddAnalysisWarning(
        analysis_warning, serialized_data=serialized_data)

  @abc.abstractmethod
  def _AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """

  @abc.abstractmethod
  def _AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (bytes): serialized form of the event data.
    """

  @abc.abstractmethod
  def _AddEventDataStream(self, event_data_stream, serialized_data=None):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
      serialized_data (bytes): serialized form of the event data stream.
    """

  def _AddEventSource(self, event_source, serialized_data=None):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
      serialized_data (Optional[bytes]): serialized form of the event source.
    """
    self._storage_writer.AddEventSource(
        event_source, serialized_data=serialized_data)

  def _AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.
    """
    self._storage_writer.AddEventTag(event_tag, serialized_data=serialized_data)

  def _AddExtractionWarning(self, extraction_warning, serialized_data=None):
    """Adds an extraction warning.

    Args:
      extraction_warning (ExtractionWarning): extraction warning.
      serialized_data (Optional[bytes]): serialized form of the extraction
          warning.
    """
    self._storage_writer.AddExtractionWarning(
        extraction_warning, serialized_data=serialized_data)

  def _AddRecoveryWarning(self, recovery_warning, serialized_data=None):
    """Adds a recovery warning.

    Args:
      recovery_warning (RecoveryWarning): recovery warning.
      serialized_data (Optional[bytes]): serialized form of the recovery
          warning.
    """
    self._storage_writer.AddRecoveryWarning(
        recovery_warning, serialized_data=serialized_data)

  def _DeserializeAttributeContainer(self, container_type, serialized_data):
    """Deserializes an attribute container.

    Args:
      container_type (str): attribute container type.
      serialized_data (bytes): serialized attribute container data.

    Returns:
      AttributeContainer: attribute container or None.

    Raises:
      IOError: if the serialized data cannot be decoded.
      OSError: if the serialized data cannot be decoded.
    """
    if not serialized_data:
      return None

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(container_type)

    try:
      serialized_string = serialized_data.decode('utf-8')
      attribute_container = self._serializer.ReadSerialized(serialized_string)

    except UnicodeDecodeError as exception:
      raise IOError('Unable to decode serialized data: {0!s}'.format(exception))

    except (TypeError, ValueError) as exception:
      # TODO: consider re-reading attribute container with error correction.
      raise IOError('Unable to read serialized data: {0!s}'.format(exception))

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(container_type)

    return attribute_container

  @abc.abstractmethod
  def MergeAttributeContainers(
      self, callback=None, maximum_number_of_containers=0):
    """Reads attribute containers from a task store into the writer.

    Args:
      callback (function[StorageWriter, AttributeContainer]): function to call
          after each attribute container is deserialized.
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.
    """

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profile.
    """
    self._storage_profiler = storage_profiler


# pylint: disable=redundant-returns-doc,redundant-yields-doc
class StorageReader(object):
  """Storage reader interface."""

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  # pylint: disable=unused-argument
  def __exit__(self, exception_type, value, traceback):
    """Make usable with "with" statement."""
    self.Close()

  @abc.abstractmethod
  def Close(self):
    """Closes the storage reader."""

  @abc.abstractmethod
  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Yields:
      AnalysisReport: analysis report.
    """

  @abc.abstractmethod
  def GetEventData(self):
    """Retrieves the event data.

    Yields:
      EventData: event data.
    """

  @abc.abstractmethod
  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """

  @abc.abstractmethod
  def GetEventDataStreams(self):
    """Retrieves the event data streams.

    Yields:
      EventDataStream: event data stream.
    """

  @abc.abstractmethod
  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """

  @abc.abstractmethod
  def GetEvents(self):
    """Retrieves the events.

    Yields:
      EventObject: event.
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves event sources.

    Yields:
      EventSourceObject: event source.
    """

  @abc.abstractmethod
  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """

  @abc.abstractmethod
  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """

  @abc.abstractmethod
  def GetExtractionWarnings(self):
    """Retrieves the extraction warnings.

    Yields:
      ExtractionWarning: extraction warning.
    """

  @abc.abstractmethod
  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """

  @abc.abstractmethod
  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """

  @abc.abstractmethod
  def GetRecoveryWarnings(self):
    """Retrieves the recovery warnings.

    Yields:
      RecoveryWarning: recovery warning.
    """

  @abc.abstractmethod
  def GetSessions(self):
    """Retrieves the sessions.

    Yields:
      Session: session.
    """

  @abc.abstractmethod
  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      EventObject: event.
    """

  @abc.abstractmethod
  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """

  @abc.abstractmethod
  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """

  @abc.abstractmethod
  def HasExtractionWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """

  @abc.abstractmethod
  def HasPreprocessingWarnings(self):
    """Determines if a store contains preprocessing warnings.

    Returns:
      bool: True if the store contains preprocessing warnings.
    """

  @abc.abstractmethod
  def HasRecoveryWarnings(self):
    """Determines if a store contains recovery warnings.

    Returns:
      bool: True if the store contains recovery warnings.
    """

  # TODO: remove, this method is kept for backwards compatibility reasons.
  @abc.abstractmethod
  def ReadSystemConfiguration(self, knowledge_base):
    """Reads system configuration information.

    The system configuration contains information about various system specific
    configuration data, for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the system configuration.
    """

  @abc.abstractmethod
  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """

  @abc.abstractmethod
  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profile.
    """


# pylint: disable=redundant-returns-doc,redundant-yields-doc
class StorageWriter(object):
  """Storage writer interface.

  Attributes:
    number_of_analysis_reports (int): number of analysis reports written.
    number_of_analysis_warnings (int): number of analysis warnings written.
    number_of_event_sources (int): number of event sources written.
    number_of_event_tags (int): number of event tags written.
    number_of_events (int): number of events written.
    number_of_extraction_warnings (int): number of extraction warnings written.
    number_of_recovery_warnings (int): number of recovery warnings written.
  """

  def __init__(
      self, session, storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(StorageWriter, self).__init__()
    self._event_data_parser_mappings = {}
    self._first_written_event_source_index = 0
    self._serializers_profiler = None
    self._session = session
    self._storage_profiler = None
    self._storage_type = storage_type
    self._task = task
    self._written_event_source_index = 0
    self.number_of_analysis_reports = 0
    self.number_of_analysis_warnings = 0
    self.number_of_event_sources = 0
    self.number_of_event_tags = 0
    self.number_of_events = 0
    self.number_of_extraction_warnings = 0
    self.number_of_preprocessing_warnings = 0
    self.number_of_recovery_warnings = 0

  @property
  def number_of_warnings(self):
    """int: number of extraction warnings written."""
    return self.number_of_extraction_warnings

  @abc.abstractmethod
  def AddAnalysisReport(self, analysis_report, serialized_data=None):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): a report.
      serialized_data (Optional[bytes]): serialized form of the analysis report.
    """

  @abc.abstractmethod
  def AddAnalysisWarning(self, analysis_warning, serialized_data=None):
    """Adds an analysis warning.

    Args:
      analysis_warning (AnalysisWarning): an analysis warning.
      serialized_data (Optional[bytes]): serialized form of the analysis
          warning.
    """

  def AddEvent(self, event, serialized_data=None):  # pylint: disable=unused-argument
    """Adds an event.

    Args:
      event(EventObject): an event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      event_data_identifier = event.GetEventDataIdentifier()
      lookup_key = event_data_identifier.CopyToString()

      parser_name = self._event_data_parser_mappings.get(lookup_key, 'N/A')
      self._session.parsers_counter[parser_name] += 1
      self._session.parsers_counter['total'] += 1

    self.number_of_events += 1

  def AddEventData(self, event_data, serialized_data=None):  # pylint: disable=unused-argument
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (Optional[bytes]): serialized form of the event data.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      identifier = event_data.GetIdentifier()
      lookup_key = identifier.CopyToString()
      parser_name = event_data.parser.split('/')[-1]
      self._event_data_parser_mappings[lookup_key] = parser_name

  @abc.abstractmethod
  def AddEventDataStream(self, event_data_stream, serialized_data=None):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
      serialized_data (Optional[bytes]): serialized form of the event data
          stream.
    """

  @abc.abstractmethod
  def AddEventSource(self, event_source, serialized_data=None):
    """Adds an event source.

    Args:
      event_source (EventSource): an event source.
      serialized_data (Optional[bytes]): serialized form of the event source.
    """

  @abc.abstractmethod
  def AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.
    """

  @abc.abstractmethod
  def AddExtractionWarning(self, extraction_warning, serialized_data=None):
    """Adds an extraction warning.

    Args:
      extraction_warning (ExtractionWarning): an extraction warning.
      serialized_data (Optional[bytes]): serialized form of the extraction
          warning.
    """

  @abc.abstractmethod
  def AddPreprocessingWarning(
      self, preprocessing_warning, serialized_data=None):
    """Adds a preprocessing warning.

    Args:
      preprocessing_warning (PreprocessingWarning): preprocessing warning.
      serialized_data (Optional[bytes]): serialized form of the preprocessing
          warning.
    """

  @abc.abstractmethod
  def AddRecoveryWarning(self, recovery_warning, serialized_data=None):
    """Adds a recovery warning.

    Args:
      recovery_warning (RecoveryWarning): a recovery warning.
      serialized_data (Optional[bytes]): serialized form of the recovery
          warning.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the storage writer."""

  @abc.abstractmethod
  def CheckTaskReadyForMerge(self, task):
    """Checks if a task is ready for merging into the store.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task is ready to be merged.
    """

  # pylint: disable=unused-argument
  def CreateTaskStorage(self, task, task_storage_format):
    """Creates a task store.

    Args:
      task (Task): task.
      task_storage_format (str): storage format to store task results.

    Returns:
      StorageWriter: storage writer for the task store.

    Raises:
      NotImplementedError: since there is no implementation.
    """
    raise NotImplementedError()

  @abc.abstractmethod
  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """

  @abc.abstractmethod
  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """

  @abc.abstractmethod
  def GetEvents(self):
    """Retrieves the events.

    Yields:
      EventObject: event.
    """

  @abc.abstractmethod
  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.
    """

  @abc.abstractmethod
  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.
    """

  @abc.abstractmethod
  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      EventObject: event.
    """

  # pylint: disable=unused-argument
  def FinalizeTaskStorage(self, task):
    """Finalizes a processed task storage.

    Args:
      task (Task): task.

    Raises:
      NotImplementedError: since there is no implementation.
    """
    raise NotImplementedError()

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage writer."""

  # pylint: disable=unused-argument
  def PrepareMergeTaskStorage(self, task):
    """Prepares a task storage for merging.

    Args:
      task (Task): task.

    Raises:
      NotImplementedError: since there is no implementation.
    """
    raise NotImplementedError()

  # pylint: disable=unused-argument
  def RemoveProcessedTaskStorage(self, task):
    """Removes a processed task storage.

    Args:
      task (Task): task.

    Raises:
      NotImplementedError: since there is no implementation.
    """
    raise NotImplementedError()

  @abc.abstractmethod
  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """

  @abc.abstractmethod
  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """

  @abc.abstractmethod
  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.
    """

  @abc.abstractmethod
  def WriteSessionConfiguration(self):
    """Writes session configuration information."""

  @abc.abstractmethod
  def WriteSessionStart(self):
    """Writes session start information."""

  @abc.abstractmethod
  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.
    """

  @abc.abstractmethod
  def WriteTaskStart(self):
    """Writes task start information."""
