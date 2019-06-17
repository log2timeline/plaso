# -*- coding: utf-8 -*-
"""The storage interface classes."""

from __future__ import unicode_literals

import abc
from plaso.lib import definitions


# pylint: disable=redundant-returns-doc,redundant-yields-doc
class BaseStore(object):
  """Storage interface.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  def __init__(self):
    """Initializes a store."""
    super(BaseStore, self).__init__()
    self.format_version = None
    self.serialization_format = None
    self.storage_type = None
    self._serializers_profiler = None
    self._storage_profiler = None

  @abc.abstractmethod
  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
    """

  @abc.abstractmethod
  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.
    """

  @abc.abstractmethod
  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
    """

  @abc.abstractmethod
  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
    """

  @abc.abstractmethod
  def AddWarning(self, warning):
    """Adds a warning.

    Args:
      warning (ExtractionWarning): warning.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the storage."""

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
  def GetEvents(self):
    """Retrieves the events.

    Yields:
      EventObject: event.
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      EventSource: event source.
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
  def GetWarnings(self):
    """Retrieves the warnings.

    Yields:
      ExtractionWarning: warning.
    """

  @abc.abstractmethod
  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """

  @abc.abstractmethod
  def HasWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """

  @abc.abstractmethod
  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage."""

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

  @abc.abstractmethod
  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.
    """

  @abc.abstractmethod
  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.
    """

  @abc.abstractmethod
  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.
    """

  @abc.abstractmethod
  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.
    """

  @abc.abstractmethod
  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.
    """


class StorageMergeReader(object):
  """Storage reader interface for merging."""

  def __init__(self, storage_writer):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    super(StorageMergeReader, self).__init__()
    self._storage_writer = storage_writer

  @abc.abstractmethod
  def MergeAttributeContainers(
      self, callback=None, maximum_number_of_containers=0):
    """Reads attribute containers from a task storage file into the writer.

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

  @abc.abstractproperty
  def format_version(self):
    """int: format version"""

  @abc.abstractproperty
  def serialization_format(self):
    """str: serialization format."""

  @abc.abstractproperty
  def storage_type(self):
    """str: storage type."""

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

  # pylint: disable=unused-argument
  def CreateTaskStorage(self, task):
    """Creates a task storage.

    Args:
      task (Task): task.

    Returns:
      StorageWriter: storage writer.

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
