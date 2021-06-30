# -*- coding: utf-8 -*-
"""Storage writer for Redis."""

from plaso.lib import definitions
from plaso.storage import writer
from plaso.storage.redis import redis_store


class RedisStorageWriter(writer.StorageWriter):
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

    if self._serializers_profiler:
      self._store.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._store.SetStorageProfiler(self._storage_profiler)

    self._store.Open(redis_client=redis_client)

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
