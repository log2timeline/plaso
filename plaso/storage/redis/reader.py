# -*- coding: utf-8 -*-
"""Redis reader."""

from plaso.lib import definitions
from plaso.storage import reader
from plaso.storage.redis import redis_store


class RedisStorageReader(reader.StorageReader):
  """Redis storage file reader."""

  def __init__(self, task):
    """Initializes a Redis Storage Reader.

    Args:
      task (Task): the task whose results the store contains.
    """
    super(RedisStorageReader, self).__init__()
    self._store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    self._store.Open(
        session_identifier=task.session_identifier,
        task_identifier=task.identifier)

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
