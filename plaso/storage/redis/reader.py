# -*- coding: utf-8 -*-
"""Redis reader."""
from __future__ import unicode_literals

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

  def IsFinalized(self):
    """Checks if the store has been finalized.

    Returns:
      bool: True if the store has been finalized.
    """
    return self._store.IsFinalized()

  def Open(self):
    """Opens the storage reader."""
    self._store.Open()

  def Close(self):
    """Closes the storage reader."""
    self._store.Close()

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return self._store.GetAnalysisReports()

  def GetEventData(self):
    """Retrieves the event data.

    Returns:
      generator(EventData): event data generator.
    """
    return self._store.GetEventData()

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (AttributeContainerIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    return self._store.GetEventDataByIdentifier(identifier)

  def GetEventDataStreams(self):
    """Retrieves the event data streams.

    Returns:
      generator(EventDataStream): event data stream generator.
    """
    return self._store.GetEventDataStreams()

  def GetEventDataStreamByIdentifier(self, identifier):
    """Retrieves a specific event data stream.

    Args:
      identifier (AttributeContainerIdentifier): event data stream identifier.

    Returns:
      EventDataStream: event data stream or None if not available.
    """
    return self._store.GetEventDataStreamByIdentifier(identifier)

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return self._store.GetEvents()

  def GetEventSources(self):
    """Retrieves event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return self._store.GetEventSources()

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (AttributeContainerIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """
    return self._store.GetEventTagByIdentifier(identifier)

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventSource): event tag generator.
    """
    return self._store.GetEventTags()

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._store.GetNumberOfAnalysisReports()

  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """
    return self._store.GetNumberOfEventSources()

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

  def GetWarnings(self):
    """Retrieves the warnings.

    Returns:
      generator(ExtractionWarning): extraction warning generator.
    """
    return self._store.GetWarnings()

  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """
    return self._store.HasAnalysisReports()

  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """
    return self._store.HasEventTags()

  def HasWarnings(self):
    """Determines if a store contains extraction warnings.

    Returns:
      bool: True if the store contains extraction warnings.
    """
    return self._store.HasWarnings()

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
