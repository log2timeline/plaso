# -*- coding: utf-8 -*-
"""The storage interface classes."""

from __future__ import unicode_literals

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
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_ERROR = (
      warnings.ExtractionError.CONTAINER_TYPE)
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_COMPLETION = sessions.SessionCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_START = sessions.SessionStart.CONTAINER_TYPE
  _CONTAINER_TYPE_SYSTEM_CONFIGURATION = (
      artifacts.SystemConfigurationArtifact.CONTAINER_TYPE)
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_ANALYSIS_REPORT,
      _CONTAINER_TYPE_EXTRACTION_ERROR,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_SESSION_COMPLETION,
      _CONTAINER_TYPE_SESSION_START,
      _CONTAINER_TYPE_SYSTEM_CONFIGURATION,
      _CONTAINER_TYPE_TASK_COMPLETION,
      _CONTAINER_TYPE_TASK_START)

  def __init__(self):
    """Initializes a store."""
    super(BaseStore, self).__init__()
    self.format_version = None
    self.serialization_format = None
    self.storage_type = None
    self._serializers_profiler = None
    self._storage_profiler = None
    self._serializer = json_serializer.JSONAttributeContainerSerializer

  @abc.abstractmethod
  def _AddAttributeContainer(self, container_type, container):
    """Adds an attribute container.

    Args:
      container_type (str): attribute container type.
      container (AttributeContainer): attribute container.
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
    """Raises if the storage file is not writable.

     Raises:
       OSError: if the store cannot be written to.
       IOError: if the store cannot be written to.
    """

  @abc.abstractmethod
  def _RaiseIfNotReadable(self):
    """Raises if the storage file is not readable.

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

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_ANALYSIS_REPORT, analysis_report)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT, event)

  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT_DATA, event_data)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT_SOURCE, event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT_TAG, event_tag)

  def AddWarning(self, warning):
    """Adds a warning.

    Args:
      warning (ExtractionWarning): warning.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EXTRACTION_WARNING, warning)

  @abc.abstractmethod
  def Close(self):
    """Closes the store."""

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_REPORT)

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

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(Event): event  generator.
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

  @abc.abstractmethod
  def GetSessions(self):
    """Retrieves the sessions.

    Yields:
      Session: session.
    """

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
  def GetWarnings(self):
    """Retrieves the warnings.

    Yields:
      ExtractionWarning: warning.
    """

  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def HasWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """
    # To support older storage versions, check for the now deprecated
    # extraction errors.
    has_errors = self._HasAttributeContainers(
        self._CONTAINER_TYPE_EXTRACTION_ERROR)
    if has_errors:
      return True

    return self._HasAttributeContainers(self._CONTAINER_TYPE_EXTRACTION_WARNING)

  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_EVENT_TAG)

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage."""

  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
    """
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

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocess
          information or the storage file is closed or read-only.
      OSError: if the storage type does not support writing preprocess
          information or the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Preprocess information not supported by storage type.')

    system_configuration = knowledge_base.GetSystemConfigurationArtifact()

    self._WriteAttributeContainer(system_configuration)

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(session_completion)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(session_start)

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      StorageNotReadableError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

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
    except UnicodeDecodeError as exception:
      raise IOError('Unable to decode serialized data: {0!s}'.format(
          exception))
    attribute_container = self._serializer.ReadSerialized(serialized_string)

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

  def __init__(self, storage_writer):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    super(StorageMergeReader, self).__init__()
    self._storage_writer = storage_writer
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None

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
    except UnicodeDecodeError as exception:
      raise IOError('Unable to decode serialized data: {0!s}'.format(
          exception))
    attribute_container = self._serializer.ReadSerialized(serialized_string)

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
  def GetWarnings(self):
    """Retrieves the warnings.

    Yields:
      ExtractionWarning: warning.
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
  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """

  @abc.abstractmethod
  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

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
  def HasWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """

  @abc.abstractmethod
  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
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
    number_of_event_sources (int): number of event sources written.
    number_of_event_tags (int): number of event tags written.
    number_of_events (int): number of events written.
    number_of_warnings (int): number of warnings written.
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
    self._first_written_event_source_index = 0
    self._serializers_profiler = None
    self._session = session
    self._storage_profiler = None
    self._storage_type = storage_type
    self._task = task
    self._written_event_source_index = 0
    self.number_of_analysis_reports = 0
    self.number_of_event_sources = 0
    self.number_of_event_tags = 0
    self.number_of_events = 0
    self.number_of_warnings = 0

  @abc.abstractmethod
  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): a report.
    """

  @abc.abstractmethod
  def AddEvent(self, event):
    """Adds an event.

    Args:
      event(EventObject): an event.
    """

  @abc.abstractmethod
  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.
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
  def AddWarning(self, warning):
    """Adds an warning.

    Args:
      warning (ExtractionWarning): a warning.
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
  def Open(self):
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

  @abc.abstractmethod
  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
    """

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
  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.
    """

  @abc.abstractmethod
  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.
    """

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
