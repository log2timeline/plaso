# -*- coding: utf-8 -*-
"""Fake (in-memory only) storage writer for testing."""

import collections
import copy
import itertools

from plaso.lib import definitions
from plaso.storage import event_heaps
from plaso.storage import identifiers
from plaso.storage import writer


class FakeStorageWriter(writer.StorageWriter):
  """Fake (in-memory only) storage writer object.

  Attributes:
    session_completion (SessionCompletion): session completion attribute
        container.
    session_configuration (SessionConfiguration): session configuration
        attribute container.
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
    self._attribute_containers = {}
    self._attribute_container_sequence_numbers = collections.Counter()
    self._is_open = False

    self.session_completion = None
    self.session_configuration = None
    self.session_start = None
    self.task_completion = None
    self.task_start = None

  @property
  def analysis_reports(self):
    """list[AnalysisReport]: analysis reports."""
    containers = self._attribute_containers.get(
        self._CONTAINER_TYPE_ANALYSIS_REPORT, {})
    return list(containers.values())

  def _GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    containers = self._attribute_containers.get(container_type, {})
    number_of_containers = len(containers)
    if index < 0 or index >= number_of_containers:
      return None

    return next(itertools.islice(
        containers.values(), index, number_of_containers))

  def _GetAttributeContainerNextSequenceNumber(self, container_type):
    """Retrieves the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: next sequence number.
    """
    self._attribute_container_sequence_numbers[container_type] += 1
    return self._attribute_container_sequence_numbers[container_type]

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage writer.')

  def AddAttributeContainer(self, container):
    """Adds a new attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    containers = self._attribute_containers.get(container.CONTAINER_TYPE, None)
    if containers is None:
      containers = collections.OrderedDict()
      self._attribute_containers[container.CONTAINER_TYPE] = containers

    next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
        container.CONTAINER_TYPE)

    identifier = identifiers.FakeIdentifier(next_sequence_number)
    container.SetIdentifier(identifier)

    lookup_key = identifier.CopyToString()

    # Make sure the fake storage preserves the state of the attribute container.
    container = copy.deepcopy(container)
    containers[lookup_key] = container

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_REPORT:
      self._UpdateAnalysisReportSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_WARNING:
      self.number_of_analysis_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      self._UpdateEventParsersSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._UpdateEventDataParsersMappings(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_SOURCE:
      self.number_of_event_sources += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG:
      self._UpdateEventLabelsSessionCounter(container)
      # TODO: maintain a mapping of event identifier to tag.

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EXTRACTION_WARNING:
      self.number_of_extraction_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_PREPROCESSING_WARNING:
      self.number_of_preprocessing_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_RECOVERY_WARNING:
      self.number_of_recovery_warnings += 1

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._is_open = False

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    containers = self._attribute_containers.get(container_type, {})

    lookup_key = identifier.CopyToString()
    return containers.get(lookup_key, None)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    containers = self._attribute_containers.get(container_type, {})
    return iter(containers.values())

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

    event_source = self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE,
        self._first_written_event_source_index)
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

    event_source = self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE, self._written_event_source_index)
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

    generator = self.GetAttributeContainers(self._CONTAINER_TYPE_EVENT)
    event_heap = event_heaps.EventHeap()

    for event_index, event in enumerate(generator):
      if (time_range and (
          event.timestamp < time_range.start_timestamp or
          event.timestamp > time_range.end_timestamp)):
        continue

      # The event index is used to ensure to sort events with the same date and
      # time and description in the order they were added to the store.
      event_heap.PushEvent(event, event_index)

    return iter(event_heap.PopEvents())

  def Open(self, **unused_kwargs):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._is_open:
      raise IOError('Storage writer already opened.')

    self._is_open = True

    event_sources = self._attribute_containers.get(
        self._CONTAINER_TYPE_EVENT_SOURCE, {})
    self._first_written_event_source_index = len(event_sources)
    self._written_event_source_index = self._first_written_event_source_index

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

  def WriteSessionConfiguration(self):
    """Writes session configuration information.


    Raises:
      IOError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
      OSError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session configuration not supported by storage type.')

    self.session_configuration = self._session.CreateSessionConfiguration()

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
