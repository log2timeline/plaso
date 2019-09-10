# -*- coding: utf-8 -*-
"""Fake storage writer for testing."""

from __future__ import unicode_literals

import copy

from plaso.lib import definitions
from plaso.storage import event_heaps
from plaso.storage import identifiers
from plaso.storage import interface


class FakeStorageWriter(interface.StorageWriter):
  """Fake storage writer object.

  Attributes:
    analysis_reports (list[AnalysisReport]): analysis reports.
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
    self._event_data = {}
    self._event_sources = []
    self._event_tags = []
    self._events = []
    self._warnings = []
    self._is_open = False
    self._task_storage_writers = {}
    self.analysis_reports = []
    self.session_completion = None
    self.session_start = None
    self.task_completion = None
    self.task_start = None

  def _PrepareAttributeContainer(self, attribute_container):
    """Prepares an attribute container for storage.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      AttributeContainer: copy of the attribute container to store in
          the fake storage.
    """
    attribute_values_hash = hash(attribute_container.GetAttributeValuesString())
    identifier = identifiers.FakeIdentifier(attribute_values_hash)
    attribute_container.SetIdentifier(identifier)

    # Make sure the fake storage preserves the state of the attribute container.
    return copy.deepcopy(attribute_container)

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage writer.')

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    analysis_report = self._PrepareAttributeContainer(analysis_report)

    self.analysis_reports.append(analysis_report)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage writer is closed or
          if the event data identifier type is not supported.
      OSError: when the storage writer is closed or
          if the event data identifier type is not supported.
    """
    self._RaiseIfNotWritable()

    # TODO: change to no longer allow event_data_identifier is None
    # after refactoring every parser to generate event data.
    event_data_identifier = event.GetEventDataIdentifier()
    if event_data_identifier:
      if not isinstance(event_data_identifier, identifiers.FakeIdentifier):
        raise IOError('Unsupported event data identifier type: {0:s}'.format(
            type(event_data_identifier)))

    event = self._PrepareAttributeContainer(event)

    self._events.append(event)
    self.number_of_events += 1

  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    event_data = self._PrepareAttributeContainer(event_data)

    identifier = event_data.GetIdentifier()
    lookup_key = identifier.CopyToString()
    self._event_data[lookup_key] = event_data

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    event_source = self._PrepareAttributeContainer(event_source)

    self._event_sources.append(event_source)
    self.number_of_event_sources += 1

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    event_identifier = event_tag.GetEventIdentifier()
    if not isinstance(event_identifier, identifiers.FakeIdentifier):
      raise IOError('Unsupported event identifier type: {0:s}'.format(
          type(event_identifier)))

    event_tag = self._PrepareAttributeContainer(event_tag)

    self._event_tags.append(event_tag)
    self.number_of_event_tags += 1

  def AddWarning(self, warning):
    """Adds a warnings.

    Args:
      warning (ExtractionWarning): warning.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    warning = self._PrepareAttributeContainer(warning)

    self._warnings.append(warning)
    self.number_of_warnings += 1

  def CheckTaskReadyForMerge(self, task):
    """Checks if a task is ready for merging into the session store.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task is ready to be merged.

    Raises:
      IOError: if the task storage type is not supported or the storage writer
          for the task does not exist.
      OSError: if the task storage type is not supported or the storage writer
          for the task does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if task.identifier not in self._task_storage_writers:
      raise IOError('Storage writer for task: {0:s} does not exist.'.format(
          task.identifier))

    # For the fake storage tasks are always ready to be merged.
    return True

  def CreateTaskStorage(self, task, task_storage_format):
    """Creates a task storage.

    Args:
      task (Task): task.
      task_storage_format (str): storage format to store task results.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      IOError: if the task storage already exists.
      OSError: if the task storage already exists.
    """
    if task.identifier in self._task_storage_writers:
      raise IOError('Storage writer for task: {0:s} already exists.'.format(
          task.identifier))

    storage_writer = FakeStorageWriter(
        self._session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)
    self._task_storage_writers[task.identifier] = storage_writer
    return storage_writer

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._is_open = False

  def GetWarnings(self):
    """Retrieves the warnings.

    Returns:
      generator(ExtractionWarning): warning generator.
    """
    return iter(self._warnings)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return iter(self._events)

  def GetEventData(self):
    """Retrieves the event data.

    Returns:
      generator(EventData): event data generator.
    """
    return iter(self._event_data.values())

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    lookup_key = identifier.CopyToString()
    return self._event_data.get(lookup_key, None)

  def GetEventSources(self):
    """Retrieves the event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return iter(self._event_sources)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTags): event tag generator.
    """
    return iter(self._event_tags)

  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage writer.')

    if self._written_event_source_index >= len(self._event_sources):
      return None

    event_source = self._event_sources[self._first_written_event_source_index]
    self._written_event_source_index = (
        self._first_written_event_source_index + 1)
    return event_source

  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage writer.')

    if self._written_event_source_index >= len(self._event_sources):
      return None

    event_source = self._event_sources[self._written_event_source_index]
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
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage writer.')

    event_heap = event_heaps.EventHeap()

    for event_index, event in enumerate(self._events):
      if (time_range and (
          event.timestamp < time_range.start_timestamp or
          event.timestamp > time_range.end_timestamp)):
        continue

      # The event index is used to ensure to sort events with the same date and
      # time and description in the order they were added to the store.
      event_heap.PushEvent(event, event_index)

    return iter(event_heap.PopEvents())

  def FinalizeTaskStorage(self, task):
    """Finalizes a processed task storage.

    Args:
      task (Task): task.

    Raises:
      IOError: if the task storage does not exist.
      OSError: if the task storage does not exist.
    """
    if task.identifier not in self._task_storage_writers:
      raise IOError('Storage writer for task: {0:s} does not exist.'.format(
          task.identifier))

  def Open(self):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._is_open:
      raise IOError('Storage writer already opened.')

    self._is_open = True

    self._first_written_event_source_index = len(self._event_sources)
    self._written_event_source_index = self._first_written_event_source_index

  def PrepareMergeTaskStorage(self, task):
    """Prepares a task storage for merging.

    Args:
      task (Task): task.

    Raises:
      IOError: if the task storage does not exist.
      OSError: if the task storage does not exist.
    """
    if task.identifier not in self._task_storage_writers:
      raise IOError('Storage writer for task: {0:s} does not exist.'.format(
          task.identifier))

  # pylint: disable=unused-argument
  def ReadPreprocessingInformation(self, knowledge_base):
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
      OSError: if the storage type does not support writing preprocessing
          information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Preprocessing information not supported by storage type.')

    # TODO: implement.

  def RemoveProcessedTaskStorage(self, task):
    """Removes a processed task storage.

    Args:
      task (Task): task.

    Raises:
      IOError: if the task storage does not exist.
      OSError: if the task storage does not exist.
    """
    if task.identifier not in self._task_storage_writers:
      raise IOError('Storage writer for task: {0:s} does not exist.'.format(
          task.identifier))

    del self._task_storage_writers[task.identifier]

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    return

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    return

  # pylint: disable=unused-argument
  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): used to store the preprocessing
          information.

    Raises:
      IOError: if the storage type does not support writing preprocessing
          information or when the storage writer is closed.
      OSError: if the storage type does not support writing preprocessing
          information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Preprocessing information not supported by storage type.')

    # TODO: implement.

  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type does not support writing a session
          completion or when the storage writer is closed.
      OSError: if the storage type does not support writing a session
          completion or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session start not supported by storage type.')

    self._session.aborted = aborted
    self.session_completion = self._session.CreateSessionCompletion()

  def WriteSessionStart(self):
    """Writes session start information.

    Raises:
      IOError: if the storage type does not support writing a session
          start or when the storage writer is closed.
      OSError: if the storage type does not support writing a session
          start or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session start not supported by storage type.')

    self.session_start = self._session.CreateSessionStart()

  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type does not support writing a task
          completion or when the storage writer is closed.
      OSError: if the storage type does not support writing a task
          completion or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Task completion not supported by storage type.')

    self._task.aborted = aborted
    self.task_completion = self._task.CreateTaskCompletion()

  def WriteTaskStart(self):
    """Writes task start information.

    Raises:
      IOError: if the storage type does not support writing a task
          start or when the storage writer is closed.
      OSError: if the storage type does not support writing a task
          start or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Task start not supported by storage type.')

    self.task_start = self._task.CreateTaskStart()
