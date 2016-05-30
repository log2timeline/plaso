# -*- coding: utf-8 -*-
"""The storage interface classes."""

import abc

from plaso.engine import profiler


class BaseStorage(object):
  """Class that defines the storage interface."""

  def __init__(self):
    """Initializes a storage object."""
    super(BaseStorage, self).__init__()
    self._profiling_sample = 0
    self._serializers_profiler = None

  @abc.abstractmethod
  def AddError(self, error):
    """Adds an error to the storage.

    Args:
      error: an error (instance of AnalysisError or ExtractionError).
    """

  @abc.abstractmethod
  def AddEvent(self, event_object):
    """Adds an event to the storage.

    Args:
      event_object: an event object (instance of EventObject).
    """

  @abc.abstractmethod
  def AddEventSource(self, event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source (instance of EventSource).
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
      profiling_type: optional profiling type.
    """
    if (profiling_type in (u'all', u'serializers') and
        not self._serializers_profiler):
      self._serializers_profiler = profiler.SerializersProfiler(u'Storage')

  @abc.abstractmethod
  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Yields:
      Analysis reports (instances of AnalysisReport).
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      An event source object (instance of EventSource).
    """

  @abc.abstractmethod
  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      An event tag object (instance of EventTag).
    """

  @abc.abstractmethod
  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      A boolean value indicating if the storage contains analysis reports.
    """

  @abc.abstractmethod
  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      A boolean value indicating if the storage contains event tags.
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
    return

  @abc.abstractmethod
  def GetEvents(self, time_range=None):
    """Retrieves events.

    Args:
      time_range: an optional time range object (instance of TimeRange).

    Yields:
      Event objects (instance of EventObject).
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves event sources.

    Yields:
      Event source objects (instance of EventSourceObject).
    """


class StorageWriter(object):
  """Class that defines the storage writer interface.

  Attributes:
    number_of_errors: an integer containing the number of errors written.
    number_of_event_sources: an integer containing the number of event
                             sources written.
    number_of_events: an integer containing the number of events written.
  """

  def __init__(self):
    """Initializes a storage writer object."""
    super(StorageWriter, self).__init__()
    self._enable_profiling = False
    self._profiling_type = u'all'
    self.number_of_errors = 0
    self.number_of_event_sources = 0
    self.number_of_events = 0

  @abc.abstractmethod
  def AddError(self, error):
    """Adds an error to the storage.

    Args:
      error: an error object (instance of AnalysisError or ExtractionError).
    """

  @abc.abstractmethod
  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report to the storage.

    Args:
      analysis_report: an analysis report object (instance of AnalysisReport).
    """

  @abc.abstractmethod
  def AddEvent(self, event_object):
    """Adds an event to the storage.

    Args:
      event_object: an event object (instance of EventObject).
    """

  @abc.abstractmethod
  def AddEventSource(self, event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source object (instance of EventSource).
    """

  @abc.abstractmethod
  def AddEventTag(self, event_tag):
    """Adds an event tag to the storage.

    Args:
      event_tag: an event tag object (instance of EventTag).
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the storage writer."""

  def DisableProfiling(self):
    """Disables profiling."""
    self._enable_profiling = False

  def EnableProfiling(self, profiling_type=u'all'):
    """Enables profiling.

    Args:
      profiling_type: optional profiling type.
    """
    self._enable_profiling = True
    self._profiling_type = profiling_type

  # TODO: remove during phased processing refactor.
  @abc.abstractmethod
  def ForceClose(self):
    """Forces the storage writer to close."""

  # TODO: remove during phased processing refactor.
  @abc.abstractmethod
  def ForceFlush(self):
    """Forces the storage writer to flush."""

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      An event source object (instance of EventSource).
    """

  @abc.abstractmethod
  def Open(self):
    """Opens the storage writer."""

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
  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start: the session start information (instance of SessionStart).
    """
