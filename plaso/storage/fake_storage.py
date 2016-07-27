# -*- coding: utf-8 -*-
"""The fake storage intended for testing."""

from plaso.lib import definitions
from plaso.storage import interface


class FakeStorageWriter(interface.StorageWriter):
  """Class that implements a fake storage writer object.

  Attributes:
    analysis_reports (list[AnalysisReport]): analysis reports.
    errors (list[ExtractionError]): extraction errors.
    event_sources (list[EventSource]): event sources.
    event_tags (list[EventTag]): event tags.
    events (list[EventObject]): event.
    session_completion (SessionCompletion): session completion attribute
        container.
    session_start (SessionStart): session start attribute container.
    task_completion (TaskCompletion): task completion attribute container.
    task_start (TaskStart): task start attribute container.
  """

  # pylint: disable=abstract-method

  def __init__(
      self, session, storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer object.

    Args:
      session (Session): session the storage changes are part of.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(FakeStorageWriter, self).__init__(
        session, storage_type=storage_type, task=task)
    self._is_open = False
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
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.analysis_reports.append(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.errors.append(error)
    self.number_of_errors += 1

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    self.events.append(event)
    self.number_of_events += 1

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

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
      event_tag (EventTag): event tag.

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

  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      EventObject: event.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to read from closed storage writer.')

    for event in sorted(self.events, key=lambda event: event.timestamp):
      if time_range and event.timestamp < time_range.start_timestamp:
        continue

      if time_range and event.timestamp > time_range.end_timestamp:
        break

      yield event

  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to read from closed storage writer.')

    if self._written_event_source_index >= len(self.event_sources):
      return

    event_source = self.event_sources[self._first_written_event_source_index]
    self._written_event_source_index = (
        self._first_written_event_source_index + 1)
    return event_source

  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to read from closed storage writer.')

    if self._written_event_source_index >= len(self.event_sources):
      return

    event_source = self.event_sources[self._written_event_source_index]
    self._written_event_source_index += 1
    return event_source

  def Open(self):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
    """
    if self._is_open:
      raise IOError(u'Storage writer already opened.')

    self._is_open = True

    self._first_written_event_source_index = len(self.event_sources)
    self._written_event_source_index = self._first_written_event_source_index

  def ReadPreprocessingInformation(self, unused_knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.

    Raises:
      IOError: if the storage type does not support writing preprocessing
               information or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Preprocessing information not supported by storage type.')

    # TODO: implement.

  def WritePreprocessingInformation(self, unused_knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocessing
               information or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Preprocessing information not supported by storage type.')

    # TODO: implement.

  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type does not support writing a session
               completion or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Session start not supported by storage type.')

    self._session.aborted = aborted
    self.session_completion = self._session.CreateSessionCompletion()

  def WriteSessionStart(self):
    """Writes session start information.

    Raises:
      IOError: if the storage type does not support writing a session
               start or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Session start not supported by storage type.')

    self.session_start = self._session.CreateSessionStart()

  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type does not support writing a task
               completion or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task completion not supported by storage type.')

    self._task.aborted = aborted
    self.task_completion = self._task.CreateTaskCompletion()

  def WriteTaskStart(self):
    """Writes task start information.

    Raises:
      IOError: if the storage type does not support writing a task
               start or when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task start not supported by storage type.')

    self.task_start = self._task.CreateTaskStart()
