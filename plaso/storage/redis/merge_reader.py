# -*- coding: utf-8 -*-
"""Redis merge reader."""

from __future__ import unicode_literals

from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage.redis import redis_store


class RedisMergeReader(interface.StorageMergeReader):
  """Redis store reader for merging."""

  def __init__(self, storage_writer, task, redis_client=None):
    """Initializes a Redis storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      task (Task): the task whose store is being merged.
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created.

    Raises:
      RuntimeError: if an add container method is missing.
    """
    super(RedisMergeReader, self).__init__(storage_writer)
    self._task_store = redis_store.RedisStore(
        definitions.STORAGE_TYPE_TASK,
        session_identifier=task.session_identifier,
        task_identifier=task.identifier)
    self._task_store.Open(redis_client=redis_client)

  def _Close(self):
    """Closes the Redis task store after merging."""
    # While all the containers have been merged, the 'merging' key is still
    # present, so we still need to remove the store.
    self._task_store.Remove()

  def _Open(self):
    """Opens the Redis task store before merging."""
    self._container_types = []
    for container_type in self._CONTAINER_TYPES:
      # pylint: disable=protected-access
      if self._task_store._HasAttributeContainers(container_type):
        self._container_types.append(container_type)
