# -*- coding: utf-8 -*-
"""Redis reader."""

from plaso.lib import definitions
from plaso.storage.redis import redis_store
from plaso.storage import interface


class RedisStorageReader(interface.StorageReader):
  """Redis storage file reader."""

  def __init__(self, task):
    """Initializes a Redis Storage Reader.

    Args:
      task (Task): the task whose results the store contains.
    """
    super(RedisStorageReader, self).__init__()
    self._store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK,
        session_identifier=task.session_identifier,
        task_identifier=task.identifier)

  def Close(self):
    """Closes the storage reader."""
    self._store.Close()

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    return self._store.GetAttributeContainers(container_type)

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

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """
    return self._store.GetAttributeContainerByIdentifier(
        self._CONTAINER_TYPE_EVENT_TAG, identifier)

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """
    return self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    return self._store.GetSortedEvents(time_range)

  def GetSessions(self):
    """Retrieves the sessions.

    Returns:
      generator(Session): session generator.
    """
    return self._store.GetSessions()

  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    return self._store.HasAttributeContainers(container_type)

  def IsFinalized(self):
    """Checks if the store has been finalized.

    Returns:
      bool: True if the store has been finalized.
    """
    return self._store.IsFinalized()

  def Open(self):
    """Opens the storage reader."""
    self._store.Open()

  # pylint: disable=unused-argument
  def ReadSystemConfiguration(self, knowledge_base):
    """Reads system configuration information.

    The system configuration contains information about various system specific
    configuration data, for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
    """
    # Not implemented by the Redis store, as it is a task store only.
    return

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._store.SetSerializersProfiler(serializers_profiler)

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profile.
    """
    self._store.SetStorageProfiler(storage_profiler)
