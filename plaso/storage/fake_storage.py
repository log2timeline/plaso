# -*- coding: utf-8 -*-
"""The fake storage intended for testing."""

import heapq

from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.storage import interface


class _EventsHeap(object):
  """Events heap."""

  def __init__(self):
    """Initializes an events heap."""
    super(_EventsHeap, self).__init__()
    self._heap = []

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      EventObject: event.
    """
    try:
      _, _, _, event = heapq.heappop(self._heap)
      return event

    except IndexError:
      return None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      EventObject: event.
    """
    event = self.PopEvent()
    while event:
      yield event
      event = self.PopEvent()

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    # TODO: replace this work-around for an event "comparable".
    event_values = event.CopyToDict()
    attributes = []
    for attribute_name, attribute_value in sorted(event_values.items()):
      if isinstance(attribute_value, dict):
        attribute_value = sorted(attribute_value.items())

      elif isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = repr(attribute_value)

      comparable = u'{0:s}: {1!s}'.format(attribute_name, attribute_value)
      attributes.append(comparable)

    comparable = u', '.join(attributes)
    event_values = sorted(event.CopyToDict().items())
    heap_values = (event.timestamp, event.timestamp_desc, comparable, event)
    heapq.heappush(self._heap, heap_values)


class FakeStorageWriter(interface.StorageWriter):
  """Class that implements a fake storage writer object.

  Attributes:
    analysis_reports (list[AnalysisReport]): analysis reports.
    errors (list[ExtractionError]): extraction errors.
    event_sources (list[EventSource]): event sources.
    event_tags (list[EventTag]): event tags.
    session_completion (SessionCompletion): session completion attribute
        container.
    session_start (SessionStart): session start attribute container.
    task_completion (TaskCompletion): task completion attribute container.
    task_start (TaskStart): task start attribute container.
  """

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
    self._errors = []
    self._events = []
    self._is_open = False
    self._task_storage_writers = {}
    self.analysis_reports = []
    self.event_sources = []
    self.event_tags = []
    self.session_completion = None
    self.session_start = None
    self.task_completion = None
    self.task_start = None

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage writer.')

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self.analysis_reports.append(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.

    Raises:
      IOError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._errors.append(error)
    self.number_of_errors += 1

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage writer is closed or
          if the event data identifier type is not supported.
    """
    self._RaiseIfNotWritable()

    self._events.append(event)
    self.number_of_events += 1

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

    Raises:
      IOError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self.event_sources.append(event_source)
    self.number_of_event_sources += 1

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self.event_tags.append(event_tag)

  def CreateTaskStorage(self, task):
    """Creates a task storage.

    Args:
      task (Task): task.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      IOError: if the task storage already exists.
    """
    if task.identifier in self._task_storage_writers:
      raise IOError(u'Storage writer for task: {0:s} already exists.'.format(
          task.identifier))

    storage_writer = FakeStorageWriter(
        self._session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)
    self._task_storage_writers[task.identifier] = storage_writer
    return storage_writer

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._is_open = False

  def GetErrors(self):
    """Retrieves the errors.

    Returns:
      generator(ExtractionError): error generator.
    """
    return iter(self._errors)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return iter(self._events)

  def GetEventSources(self):
    """Retrieves the event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return iter(self.event_sources)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTags): event tag generator.
    """
    return iter(self.event_tags)

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

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError(u'Unable to read from closed storage writer.')

    events_heap = _EventsHeap()

    for event in self._events:
      if (time_range and (
          event.timestamp < time_range.start_timestamp or
          event.timestamp > time_range.end_timestamp)):
        continue

      events_heap.PushEvent(event)

    return iter(events_heap.PopEvents())

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

  def PrepareMergeTaskStorage(self, task):
    """Prepares a task storage for merging.

    Args:
      task (Task): task.

    Raises:
      IOError: if the task storage does not exist.
    """
    if task.identifier not in self._task_storage_writers:
      raise IOError(u'Storage writer for task: {0:s} does not exist.'.format(
          task.identifier))

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
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError(u'Preprocessing information not supported by storage type.')

    # TODO: implement.

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profile.
    """
    pass

  def WritePreprocessingInformation(self, unused_knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocessing
          information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

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
    self._RaiseIfNotWritable()

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
    self._RaiseIfNotWritable()

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
    self._RaiseIfNotWritable()

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
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError(u'Task start not supported by storage type.')

    self.task_start = self._task.CreateTaskStart()
