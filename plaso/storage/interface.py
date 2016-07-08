# -*- coding: utf-8 -*-
"""The storage interface classes."""

import abc

from plaso.engine import profiler
from plaso.lib import definitions


class BaseStorage(object):
  """Class that defines the storage interface."""

  def __init__(self):
    """Initializes a storage object."""
    super(BaseStorage, self).__init__()
    self._profiling_sample = 0
    self._serializers_profiler = None

  @abc.abstractmethod
  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.
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
  def Close(self):
    """Closes the storage."""

  def DisableProfiling(self):
    """Disables profiling."""
    self._serializers_profiler = None

  def EnableProfiling(self, profiling_type=u'all'):
    """Enables profiling.

    Args:
      profiling_type (Optional[str]): type of profiling to enable.
    """
    if (profiling_type in (u'all', u'serializers') and
        not self._serializers_profiler):
      self._serializers_profiler = profiler.SerializersProfiler(u'Storage')

  @abc.abstractmethod
  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Yields:
      AnalysisReport: analysis report.
    """

  @abc.abstractmethod
  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      EventObject: event.
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      EventSource: event source.
    """

  @abc.abstractmethod
  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """

  @abc.abstractmethod
  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      bool: True if the storage contains analysis reports.
    """

  @abc.abstractmethod
  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage."""


class StorageReader(object):
  """Class that defines the storage reader interface."""

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
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
  def GetErrors(self):
    """Retrieves the errors.

    Yields:
      ExtractionError: error.
    """

  @abc.abstractmethod
  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      EventObject: event.
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves event sources.

    Yields:
      Event source objects (instance of EventSourceObject).
    """

  @abc.abstractmethod
  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      An event tag object (instance of EventTag).
    """


class StorageWriter(object):
  """Class that defines the storage writer interface.

  Attributes:
    number_of_errors: an integer containing the number of errors written.
    number_of_event_sources: an integer containing the number of event
                             sources written.
    number_of_events: an integer containing the number of events written.
  """

  def __init__(
      self, session, storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer object.

    Args:
      session (Session): session the storage changes are part of.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(StorageWriter, self).__init__()
    self._enable_profiling = False
    self._event_source_index = 0
    self._profiling_type = u'all'
    self._session = session
    self._storage_type = storage_type
    self._task = task
    self.number_of_errors = 0
    self.number_of_event_sources = 0
    self.number_of_events = 0

  @abc.abstractmethod
  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): a report.
    """

  @abc.abstractmethod
  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): an error.
    """

  @abc.abstractmethod
  def AddEvent(self, event_object):
    """Adds an event.

    Args:
      event_object (EventObject): an event.
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
  def Close(self):
    """Closes the storage writer."""

  def CreateTaskStorage(self, unused_task_name):
    """Creates a task storage.

    Args:
      task_name (str): unique name of the task.

    Returns:
      StorageWriter: storage writer.

    Raises:
      NotImplementedError: since there is no implementation.
    """
    raise NotImplementedError()

  def DisableProfiling(self):
    """Disables profiling."""
    self._enable_profiling = False

  def EnableProfiling(self, profiling_type=u'all'):
    """Enables profiling.

    Args:
      profiling_type (Optional[str]): type of profiling to enable.
    """
    self._enable_profiling = True
    self._profiling_type = profiling_type

  @abc.abstractmethod
  def GetNextEventSource(self):
    """Retrieves the next event source.

    Returns:
      EventSource: event source.
    """

  def MergeFromStorage(self, storage_reader):
    """Merges data from a storage reader into the writer.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    for event_source in storage_reader.GetEventSources():
      self.AddEventSource(event_source)

    for event in storage_reader.GetEvents():
      self.AddEvent(event)

    for event_tag in storage_reader.GetEventTags():
      self.AddEventTag(event_tag)

    for error in storage_reader.GetErrors():
      self.AddError(error)

    for analysis_report in storage_reader.GetAnalysisReports():
      self.AddAnalysisReport(analysis_report)

  @abc.abstractmethod
  def Open(self):
    """Opens the storage writer."""

  def PrepareMergeTaskStorage(self, unsused_task_name):
    """Prepares a task storage for merging.

    Args:
      task_name (str): unique name of the task.

    Raises:
      IOError: if the storage type is not supported or
               if the temporary path for the task storage does no exist.
    """
    raise NotImplementedError()

  def SetEnableProfiling(self, enable_profiling, profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_type: optional profiling type.
    """
    self._enable_profiling = enable_profiling
    self._profiling_type = profiling_type

  @abc.abstractmethod
  def WriteSessionCompletion(self):
    """Writes session completion information."""

  @abc.abstractmethod
  def WriteSessionStart(self):
    """Writes session start information."""

  @abc.abstractmethod
  def WriteTaskCompletion(self):
    """Writes task completion information."""

  @abc.abstractmethod
  def WriteTaskStart(self):
    """Writes task start information."""
