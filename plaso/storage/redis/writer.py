# -*- coding: utf-8 -*-
"""Storage writer for Redis."""

from plaso.storage import writer
from plaso.storage.redis import redis_store


class RedisStorageWriter(writer.StorageWriter):
  """Redis-based storage writer."""

  # pylint: disable=redundant-returns-doc,useless-return
  def GetFirstWrittenEventData(self):
    """Retrieves the first event data that was written after open.

    Using GetFirstWrittenEventData and GetNextWrittenEventData newly
    added event data can be retrieved in order of addition.

    Returns:
      EventData: None as there are no newly written event data.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return None

  # pylint: disable=redundant-returns-doc,useless-return
  def GetNextWrittenEventData(self):
    """Retrieves the next event data that was written after open.

    Returns:
      EventData: None as there are no newly written event data.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return None

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

  # pylint: disable=arguments-differ
  def Open(
      self, redis_client=None, session_identifier=None, task_identifier=None,
      **unused_kwargs):
    """Opens the storage writer.

    Args:
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created. If no client is specified a new client
          will be opened connected to the Redis instance specified by 'url'.
      session_identifier (Optional[str]): session identifier.
      task_identifier (Optional[str]): task identifier.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._store:
      raise IOError('Storage writer already opened.')

    self._store = redis_store.RedisStore()

    if self._serializers_profiler:
      self._store.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._store.SetStorageProfiler(self._storage_profiler)

    self._store.Open(
        redis_client=redis_client, session_identifier=session_identifier,
        task_identifier=task_identifier)
