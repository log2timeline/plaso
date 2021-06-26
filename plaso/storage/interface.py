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

  # TODO: is protected method still needed? remove?
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
  def _RaiseIfNotReadable(self):
    """Raises if the store is not readable.

     Raises:
       OSError: if the store cannot be read from.
       IOError: if the store cannot be read from.
    """

  @abc.abstractmethod
  def _RaiseIfNotWritable(self):
    """Raises if the store is not writable.

     Raises:
       OSError: if the store cannot be written to.
       IOError: if the store cannot be written to.
    """

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

  @abc.abstractmethod
  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """

  def AddAttributeContainer(self, container):
    """Adds an attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      OSError: if the store cannot be written to.
      IOError: if the store cannot be written to.
    """
    self._RaiseIfNotWritable()
    self._WriteNewAttributeContainer(container)

  @abc.abstractmethod
  def Close(self):
    """Closes the store."""

  @abc.abstractmethod
  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the store is closed or if an unsupported identifier is
          provided.
      OSError: when the store is closed or if an unsupported identifier is
          provided.
    """

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.

    Raises:
      IOError: when the store is closed.
      OSError: when the store is closed.
    """
    return self._GetAttributeContainers(container_type)

  @abc.abstractmethod
  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.
    """

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

    if self.HasAttributeContainers(self._CONTAINER_TYPE_SESSION_CONFIGURATION):
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

  @abc.abstractmethod
  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """

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
    if self.HasAttributeContainers(self._CONTAINER_TYPE_SYSTEM_CONFIGURATION):
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
          completion or if the store cannot be written to.
      OSError: if the storage type does not support writing a session
          completion or if the store cannot be written to.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session completion not supported by storage type.')

    self._WriteNewAttributeContainer(session_completion)

  def WriteSessionConfiguration(self, session_configuration):
    """Writes session configuration information.

    Args:
      session_configuration (SessionConfiguration): session configuration
          information.

     Raises:
       OSError: if the store cannot be written to.
       IOError: if the store cannot be written to.
    """
    self._RaiseIfNotWritable()

    if not self.HasAttributeContainers(
        self._CONTAINER_TYPE_SYSTEM_CONFIGURATION):
      self._WriteNewAttributeContainer(session_configuration)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.

    Raises:
      IOError: if the storage type does not support writing a session
          start or if the store cannot be written to.
      OSError: if the storage type does not support writing a session
          start or if the store cannot be written to.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session start not supported by storage type.')

    self._WriteNewAttributeContainer(session_start)

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: if the storage type does not support writing a task
          completion or if the store cannot be written to.
      OSError: if the storage type does not support writing a task
          completion or if the store cannot be written to.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Task start not supported by storage type.')

    self._WriteNewAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      IOError: if the storage type does not support writing a task
          start or if the store cannot be written to.
      OSError: if the storage type does not support writing a task
          start or if the store cannot be written to.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Task completion not supported by storage type.')

    self._WriteNewAttributeContainer(task_start)


# pylint: disable=redundant-returns-doc,redundant-yields-doc
class StorageReader(object):
  """Storage reader interface."""

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
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

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
  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
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
  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
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
  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
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
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

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

  def _UpdateAnalysisReportSessionCounter(self, analysis_report):
    """Updates the analysis report session counter.

    Args:
      analysis_report (AnalysisReport): a report.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      report_identifier = analysis_report.plugin_name
      self._session.analysis_reports_counter['total'] += 1
      self._session.analysis_reports_counter[report_identifier] += 1

    self.number_of_analysis_reports += 1

  def _UpdateEventLabelsSessionCounter(self, event_tag):
    """Updates the event labels session counter.

    Args:
      event_tag (EventTag): an event tag.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      self._session.event_labels_counter['total'] += 1
      for label in event_tag.labels:
        self._session.event_labels_counter[label] += 1

    self.number_of_event_tags += 1

  def _UpdateEventDataParsersMappings(self, event_data):
    """Updates the event data parsers mappings.

    Args:
      event_data (EventData): event data.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      identifier = event_data.GetIdentifier()
      lookup_key = identifier.CopyToString()
      parser_name = event_data.parser.split('/')[-1]
      self._event_data_parser_mappings[lookup_key] = parser_name

  def _UpdateEventParsersSessionCounter(self, event):
    """Updates the event parsers session counter.

    Args:
      event (EventObject): an event.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      event_data_identifier = event.GetEventDataIdentifier()
      lookup_key = event_data_identifier.CopyToString()

      parser_name = self._event_data_parser_mappings.get(lookup_key, 'N/A')
      self._session.parsers_counter[parser_name] += 1
      self._session.parsers_counter['total'] += 1

    self.number_of_events += 1

  @abc.abstractmethod
  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): a report.
    """

  @abc.abstractmethod
  def AddAnalysisWarning(self, analysis_warning):
    """Adds an analysis warning.

    Args:
      analysis_warning (AnalysisWarning): an analysis warning.
    """

  @abc.abstractmethod
  def AddAttributeContainer(self, container):
    """Adds an attribute container.

    Args:
      container (AttributeContainer): attribute container.
    """

  @abc.abstractmethod
  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): an event.
    """

  @abc.abstractmethod
  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.
    """

  @abc.abstractmethod
  def AddEventDataStream(self, event_data_stream):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
    """

  @abc.abstractmethod
  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): an event source.
    """

  @abc.abstractmethod
  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.
    """

  @abc.abstractmethod
  def AddExtractionWarning(self, extraction_warning):
    """Adds an extraction warning.

    Args:
      extraction_warning (ExtractionWarning): an extraction warning.
    """

  @abc.abstractmethod
  def AddPreprocessingWarning(
      self, preprocessing_warning):
    """Adds a preprocessing warning.

    Args:
      preprocessing_warning (PreprocessingWarning): preprocessing warning.
    """

  @abc.abstractmethod
  def AddRecoveryWarning(self, recovery_warning):
    """Adds a recovery warning.

    Args:
      recovery_warning (RecoveryWarning): a recovery warning.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the storage writer."""

  @abc.abstractmethod
  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
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

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage writer."""

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
