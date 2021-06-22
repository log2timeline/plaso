# -*- coding: utf-8 -*-
"""Storage writer for Redis."""

from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage.redis import redis_store


class RedisStorageWriter(interface.StorageWriter):
  """Redis-based storage writer."""

  def __init__(
      self, session, storage_type=definitions.STORAGE_TYPE_TASK, task=None):
    """Initializes a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      storage_type (Optional[str]): storage type.
      task (Optional[Task]): task.

    Raises:
      RuntimeError: if no task is provided.
    """
    if not task:
      raise RuntimeError('Task required.')

    super(RedisStorageWriter, self).__init__(
        session=session, storage_type=storage_type, task=task)

    self._redis_namespace = '{0:s}-{1:s}'.format(
        task.session_identifier, task.identifier)
    self._store = None

  # pylint: disable=arguments-differ
  def Open(self, redis_client=None, **unused_kwargs):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._store:
      raise IOError('Storage writer already opened.')

    self._store = redis_store.RedisStore(
        storage_type=self._storage_type,
        session_identifier=self._task.session_identifier,
        task_identifier=self._task.identifier)

    self._store.Open(redis_client=redis_client)

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Storage writer is not open.')

    self._store.Finalize()
    self._store = None

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): a report.
    """
    self._store.AddAttributeContainer(analysis_report)

    self._UpdateAnalysisReportSessionCounter(analysis_report)

  def AddAnalysisWarning(self, analysis_warning):
    """Adds an analysis warning.

    Args:
      analysis_warning (AnalysisWarning): an analysis warning.
    """
    self._store.AddAttributeContainer(analysis_warning)

  def AddAttributeContainer(self, container):
    """Adds an attribute container.

    Args:
      container (AttributeContainer): attribute container.
    """
    self._store.AddAttributeContainer(container)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event(EventObject): an event.
    """
    # TODO: refactor to use AddAttributeContainer
    self._store.AddEvent(event)

    self._UpdateEventParsersSessionCounter(event)

  def AddEventData(self, event_data):
    """Adds an event data.

    Args:
      event_data(EventData): an event.
    """
    self._store.AddAttributeContainer(event_data)

    self._UpdateEventDataParsersMappings(event_data)

  def AddEventDataStream(self, event_data_stream):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
    """
    self._store.AddAttributeContainer(event_data_stream)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): an event source.
    """
    self._store.AddAttributeContainer(event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.
    """
    self._store.AddAttributeContainer(event_tag)

    self._UpdateEventLabelsSessionCounter(event_tag)

  def AddExtractionWarning(self, extraction_warning):
    """Adds an extraction warning.

    Args:
      extraction_warning (ExtractionWarning): an extraction warning.
    """
    self._store.AddAttributeContainer(extraction_warning)

  def AddPreprocessingWarning(self, preprocessing_warning):
    """Adds a preprocessing warning.

    Args:
      preprocessing_warning (PreprocessingWarning): preprocessing warning.
    """
    self._store.AddAttributeContainer(preprocessing_warning)

  def AddRecoveryWarning(self, recovery_warning):
    """Adds a recovery warning.

    Args:
      recovery_warning (RecoveryWarning): a recovery warning.
    """
    self._store.AddAttributeContainer(recovery_warning)

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    return self._store.GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_DATA, identifier)

  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """
    return self._store.GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_DATA_STREAM, identifier)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return self._store.GetAttributeContainers(self._CONTAINER_TYPE_EVENT)

  # pylint: disable=redundant-returns-doc,useless-return
  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: None as there are no newly written event sources.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return None

  # pylint: disable=redundant-returns-doc,useless-return
  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: None as there are no newly written event sources.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return None

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return self._store.GetSortedEvents(time_range=time_range)

  def ReadSystemConfiguration(self, knowledge_base):
    """Reads system configuration information.

    The system configuration contains information about various system specific
    configuration data, for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.

    Raises:
      IOError: always, as the Redis store does not support preprocessing
          information.
      OSError: always, as the Redis store does not support preprocessing
          information.
    """
    raise IOError('Preprocessing information not supported by the redis store.')

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_profiler = storage_profiler

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: always as the Redis store does not support preprocessing
          information.
      OSError: always as the Redis store does not support preprocessing
          information.
    """
    raise IOError(
        'Preprocessing information is not supported by the redis store.')

  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: always, as the Redis store does not support writing a session
          completion.
      OSError: always, as the Redis store does not support writing a session
          completion.
    """
    raise IOError('Session completion is not supported by the redis store.')

  def WriteSessionConfiguration(self):
    """Writes session configuration information.

    Raises:
      IOError: always, as the Redis store does not support writing a session
          configuration.
      OSError: always, as the Redis store does not support writing a session
          configuration.
    """
    raise IOError('Session configuration is not supported by the redis store.')

  def WriteSessionStart(self):
    """Writes session start information.

    Raises:
      IOError: always, as the Redis store does not support writing a session
          start.
      OSError: always, as the Redis store does not support writing a session
          start.
    """
    raise IOError('Session start is not supported by the redis store.')

  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Only task storage is supported by the redis store.')

    self._task.aborted = aborted
    task_completion = self._task.CreateTaskCompletion()
    self._store.WriteTaskCompletion(task_completion)

  def WriteTaskStart(self):
    """Writes task start information.

    Raises:
      IOError: if the storage type does not support writing a task
          start or when the storage writer is closed.
      OSError: if the storage type does not support writing a task
          start or when the storage writer is closed.
    """
    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Only task storage is supported by the redis store.')

    task_start = self._task.CreateTaskStart()
    self._store.WriteTaskStart(task_start)
