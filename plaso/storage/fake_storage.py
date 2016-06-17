# -*- coding: utf-8 -*-
"""The fake storage intended for testing."""

from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage import interface


class FakeStorageWriter(interface.StorageWriter):
  """Class that implements a fake storage writer object.

  Attributes:
    analysis_reports: a list of analysis reports (instances of AnalysisReport).
    errors: a list of error objects (instances of AnalysisError or
            ExtractionError).
    event_sources: a list of event sources (instances of EventSource).
    event_tags: a list of event tags (instances of EventTag).
    events: a list of event objects (instances of EventObject).
    session_completion: session completion information (instance of
                        SessionCompletion).
    session_start: session start information (instance of SessionStart).
  """

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a storage writer object.

    Args:
      storage_type: optional string containing the storage type.
    """
    super(FakeStorageWriter, self).__init__()
    self._is_open = False
    self._session_identifier = None
    self._storage_type = storage_type
    self._task_identifier = None
    self.analysis_reports = []
    self.errors = []
    self.event_sources = []
    self.event_tags = []
    self.events = []
    self.session_completion = None
    self.session_start = None
    self.task_completion = None
    self.task_start = None

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report: an analysis report object (instance of AnalysisReport).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.analysis_reports.append(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error: an error object (instance of AnalysisError or ExtractionError).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.errors.append(error)
    self.number_of_errors += 1

  def AddEvent(self, event_object):
    """Adds an event object.

    Args:
      event_object: an event object (instance of EventObject).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.events.append(event_object)
    self.number_of_events += 1

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source: an event source object (instance of EventSource).

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.event_sources.append(event_source)
    self.number_of_event_sources += 1

  def AddEventTag(self, event_tag):
    """Adds an event tag.

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

  def CreateTaskStorageWriter(self, unused_task_name):
    """Creates a task storage writer.

    Args:
      task_name: a string containing a unique name of the task.

    Returns:
      A storage writer object (instance of StorageWriter).

    Raises:
      NotImplementedError: since there is no implementation.
    """
    raise NotImplementedError()

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
      IOError: if the storage type does not support writing a session
               completion or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Session completion not supported by storage type.')

    self.session_completion = sessions.SessionCompletion(
        self._session_identifier)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start: the session start information (instance of SessionStart).

    Raises:
      IOError: if the storage type does not support writing a session
               start or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Session start not supported by storage type.')

    self.session_start = session_start
    self._session_identifier = session_start.identifier

  def WriteTaskCompletion(self):
    """Writes task completion information.

    Raises:
      IOError: if the storage type does not support writing a task
               completion or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task completion not supported by storage type.')

    self.task_completion = tasks.TaskCompletion(
        self._session_identifier, self._task_identifier)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start: the task start information (instance of TaskStart).

    Raises:
      IOError: if the storage type does not support writing a task
               start or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task start not supported by storage type.')

    self.task_start = task_start
    self._session_identifier = task_start.identifier
    self._task_identifier = task_start.identifier
