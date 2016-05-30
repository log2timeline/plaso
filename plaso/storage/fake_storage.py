# -*- coding: utf-8 -*-
"""The fake storage intended for testing."""

from plaso.containers import sessions
from plaso.storage import interface


class FakeStorageWriter(interface.StorageWriter):
  """Class that implements a fake storage writer object.

  Attributes:
    analysis_reports: a list of analysis reports (instances of AnalysisReport).
    events: a list of event objects (instances of EventObject).
    event_sources: a list of event sources (instances of EventSource).
    event_tags: a list of event tags (instances of EventTag).
    session_completion: session completion information (instance of
                        SessionCompletion).
    session_start: session start information (instance of SessionStart).
  """

  # pylint: disable=abstract-method

  def __init__(self):
    """Initializes a storage writer object."""
    super(FakeStorageWriter, self).__init__()
    self._is_open = False
    self._session_identifier = None
    self.analysis_reports = []
    self.event_sources = []
    self.event_tags = []
    self.events = []
    self.session_completion = None
    self.session_start = None

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report to the storage.

    Args:
      analysis_report: an analysis report object (instance of AnalysisReport).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.analysis_reports.append(analysis_report)

  def AddEvent(self, event_object):
    """Adds an event object to the storage.

    Args:
      event_object: an event object (instance of EventObject).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.events.append(event_object)

  def AddEventSource(self, event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source object (instance of EventSource).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.event_sources.append(event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag to the storage.

    Args:
      event_tag: an event tag object (instance of EventTag).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.event_tags.append(event_tag)

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self._is_open = False

  # TODO: remove during phased processing refactor.
  def ForceClose(self):
    """Forces the storage writer to close.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self._is_open = False

  # TODO: remove during phased processing refactor.
  def ForceFlush(self):
    """Forces the storage writer to flush.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      An event source object (instance of EventSource).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    for event_source in self.event_sources:
      yield event_source

  def Open(self):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
    """
    if self._is_open:
      raise IOError(u'Storage writer already opened.')

    self._is_open = True

  # TODO: remove during phased processing refactor.
  def WritePreprocessObject(self, unused_preprocess_object):
    """Writes a preprocessing object.

    Args:
      preprocess_object: a preprocess object (instance of PreprocessObject).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

  def WriteSessionCompletion(self):
    """Writes session completion information.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.session_completion = sessions.SessionCompletion(
        self._session_identifier)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start: the session start information (instance of SessionStart).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.session_start = session_start
    self._session_identifier = session_start.identifier
