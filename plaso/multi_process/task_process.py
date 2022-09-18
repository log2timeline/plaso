# -*- coding: utf-8 -*-
"""Base class for a process that handles tasks used in multi-processing."""

import os

from plaso.lib import definitions
from plaso.multi_process import base_process
from plaso.storage import factory as storage_factory

try:
  # pylint: disable=ungrouped-imports
  import redis
  from plaso.storage.redis import redis_store
except ModuleNotFoundError:
  redis = None
  redis_store = None


class MultiProcessTaskProcess(base_process.MultiProcessBaseProcess):
  """Interface for multi-processing process that handles tasks."""

  # pylint: disable=abstract-method

  def __init__(
      self, processing_configuration, enable_sigsegv_handler=False, **kwargs):
    """Initializes a process.

    Args:
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      kwargs (dict[str,object]): keyword arguments to pass to
          multiprocessing.Process.
    """
    processed_task_storage_path = None
    if processing_configuration.task_storage_path:
      processed_task_storage_path = os.path.join(
          processing_configuration.task_storage_path, 'processed')

    super(MultiProcessTaskProcess, self).__init__(
        processing_configuration, **kwargs)
    self._processed_task_storage_path = processed_task_storage_path
    self._storage_factory = storage_factory.StorageFactory
    self._task_storage_path = processing_configuration.task_storage_path

  def _FinalizeTaskStorageWriter(self, task_storage_format, task):
    """Finalizes a storage writer for a task.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Raises:
      IOError: if the SQLite task storage file cannot be renamed.
      OSError: if the SQLite task storage file cannot be renamed.
    """
    if task.storage_format == definitions.STORAGE_FORMAT_REDIS and redis_store:
      url = redis_store.RedisStore.DEFAULT_REDIS_URL
      redis_client = redis.from_url(url=url, socket_timeout=60)
      redis_client.client_setname('task_process')

      redis_hash_name = self._GetProcessedRedisHashName(task.session_identifier)
      redis_client.hset(redis_hash_name, key=task.identifier, value=b'true')

    elif task.storage_format == definitions.STORAGE_FORMAT_SQLITE:
      storage_file_path = self._GetTaskStorageFilePath(
          task_storage_format, task)
      processed_storage_file_path = self._GetProcessedStorageFilePath(
          task_storage_format, task)

      try:
        os.rename(storage_file_path, processed_storage_file_path)
      except OSError as exception:
        raise IOError((
            'Unable to rename task storage file: {0:s} with error: '
            '{1!s}').format(storage_file_path, exception))

  def _GetProcessedRedisHashName(self, session_identifier):
    """Retrieves the Redis hash name of a processed task store.

    Args:
      session_identifier (str): the identifier of the session the tasks are
          part of.

    Returns:
      str: Redis hash name of a task store.
    """
    return '{0:s}-processed'.format(session_identifier)

  def _GetProcessedStorageFilePath(self, task_storage_format, task):
    """Retrieves the path of a task storage file in the processed directory.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Returns:
      str: path of a task storage file in the processed directory or None if
          not est.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      filename = '{0:s}.plaso'.format(task.identifier)
      return os.path.join(self._processed_task_storage_path, filename)

    return None

  def _GetTaskStorageFilePath(self, task_storage_format, task):
    """Retrieves the path of a task storage file in the temporary directory.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Returns:
      str: path of a task storage file in the temporary directory or None if
          not set.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      filename = '{0:s}.plaso'.format(task.identifier)
      return os.path.join(self._task_storage_path, filename)

    return None
