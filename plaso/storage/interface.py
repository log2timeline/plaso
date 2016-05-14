# -*- coding: utf-8 -*-
"""The storage interface classes."""

import abc


class StorageObject(object):
  """Class that defines the storage object."""

  @abc.abstractmethod
  def AddEventObject(self, event_object):
    """Adds an event object to the storage.

    Args:
      event_object: an event object (instance of EventObject).

    Raises:
      IOError: when the event object cannot be added.
    """

  @abc.abstractmethod
  def AddEventSource(self, event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source (instance of EventSource).

    Raises:
      IOError: when the event source cannot be added.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the storage."""

  @abc.abstractmethod
  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Yields:
      Analysis reports (instances of AnalysisReport).

    Raises:
      IOError: if the analysis reports cannot be retrieved.
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      An event source object (instance of EventSource).

    Raises:
      IOError: if the event sources cannot be retrieved.
    """

  @abc.abstractmethod
  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      An event tag object (instance of EventTag).

    Raises:
      IOError: if the event tags cannot be retrieved.
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
  def Open(self):
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
    number_of_event_sources: an integer containing the number of event
                             sources written.
  """

  def __init__(self):
    """Initializes a storage writer object."""
    super(StorageWriter, self).__init__()
    self._enable_profiling = False
    self._profiling_type = u'all'
    self.number_of_event_sources = 0

  @abc.abstractmethod
  def AddEvent(self, event_object):
    """Adds an event object to the storage.

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
  def Close(self):
    """Closes the storage writer."""

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
