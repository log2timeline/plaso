# -*- coding: utf-8 -*-
"""Redis storage reader."""

from plaso.storage import reader
from plaso.storage.redis import redis_store


class RedisStorageReader(reader.StorageReader):
  """Redis storage file reader."""

  def __init__(self, session_identifier, task_identifier, redis_client=None):
    """Initializes a Redis storage reader.

    Args:
      session_identifier (str): session identifier.
      task_identifier (str): task identifier.
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created. If no client is specified a new client
          will be opened connected to the Redis instance specified by 'url'.
    """
    super(RedisStorageReader, self).__init__()
    self._store = redis_store.RedisStore()
    self._store.Open(
        redis_client=redis_client, session_identifier=session_identifier,
        task_identifier=task_identifier)
