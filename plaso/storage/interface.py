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
