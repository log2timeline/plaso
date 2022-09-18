# -*- coding: utf-8 -*-
"""The task-based multi-process processing engine."""

import os
import shutil
import tempfile

from plaso.lib import definitions
from plaso.multi_process import engine
from plaso.storage import factory as storage_factory

try:
  # pylint: disable=ungrouped-imports
  import redis
  from plaso.storage.redis import redis_store
except ModuleNotFoundError:
  redis = None
  redis_store = None


class TaskMultiProcessEngine(engine.MultiProcessEngine):
  """Task-based multi-process engine base.

  This class contains functionality to:
  * manage task storage used to store task results.
  """

  # pylint: disable=abstract-method

  def __init__(self):
    """Initializes a task-based multi-process engine."""
    super(TaskMultiProcessEngine, self).__init__()
    self._merge_task_storage_path = None
    self._processing_configuration = None
    self._processed_task_storage_path = None
    self._redis_client = None
    self._storage_file_path = None
    self._task_storage_path = None

  # TODO: remove, currently only used by psort.
  def _CheckTaskReadyForMerge(self, task_storage_format, task):
    """Checks if a task is ready for merging with this session storage.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Returns:
      bool: True if the task is ready to be merged.

    Raises:
      IOError: if the size of the SQLite task storage file cannot be determined.
      OSError: if the size of the SQLite task storage file cannot be determined.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      processed_storage_file_path = self._GetProcessedStorageFilePath(task)

      try:
        stat_info = os.stat(processed_storage_file_path)
      except (IOError, OSError):
        return False

      task.storage_file_size = stat_info.st_size
      return True

    return False

  def _GetMergeTaskStorage(self, task_storage_format, task):
    """Retrieves a task store ready to be merged with the session store.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Returns:
      StorageReader: storage reader of the task storage.

    Raises:
      IOError: if the temporary path for the task storage does not exist or
          if the temporary path for the task storage doe not refers to a file.
      OSError: if the temporary path for the task storage does not exist or
          if the temporary path for the task storage doe not refers to a file.
    """
    merge_storage_file_path = self._GetMergeTaskStorageFilePath(
        task_storage_format, task)

    if task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      if not self._merge_task_storage_path:
        raise IOError('Missing merge task storage path.')

      if not os.path.isfile(merge_storage_file_path):
        raise IOError('Merge task storage path is not a file.')

    task_storage_reader = (
        storage_factory.StorageFactory.CreateTaskStorageReader(
            task_storage_format, task, merge_storage_file_path))
    task_storage_reader.SetStorageProfiler(self._storage_profiler)

    return task_storage_reader

  def _GetMergeTaskStorageRedisHashName(self, task):
    """Retrieves the Redis hash name of a task store that should be merged.

    Args:
      task (Task): task the storage changes are part of.

    Returns:
      str: Redis hash name of a task store.
    """
    return '{0:s}-merge'.format(task.session_identifier)

  def _GetMergeTaskStorageFilePath(self, task_storage_format, task):
    """Retrieves the path of a task storage file in the merge directory.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Returns:
      str: path of a task storage file file in the merge directory or None if
          not set.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      filename = '{0:s}.plaso'.format(task.identifier)
      return os.path.join(self._merge_task_storage_path, filename)

    return None

  def _GetProcessedRedisHashName(self, session_identifier):
    """Retrieves the Redis hash name of a processed task store.

    Args:
      session_identifier (str): the identifier of the session the tasks are
          part of.

    Returns:
      str: Redis hash name of a task store.
    """
    return '{0:s}-processed'.format(session_identifier)

  def _GetProcessedStorageFilePath(self, task):
    """Retrieves the path of a task storage file in the processed directory.

    Args:
      task (Task): task the storage changes are part of.

    Returns:
      str: path of a task storage file in the processed directory.
    """
    filename = '{0:s}.plaso'.format(task.identifier)
    return os.path.join(self._processed_task_storage_path, filename)

  def _GetProcessedTaskIdentifiers(
      self, task_storage_format, session_identifier):
    """Identifiers for tasks which have been processed.

    Args:
      task_storage_format (str): storage format used to store task results.
      session_identifier (str): the identifier of the session the tasks are
          part of.

    Returns:
      list[str]: task identifiers that are processed.

    Raises:
      IOError: if the temporary path for the task storage does not exist.
      OSError: if the temporary path for the task storage does not exist.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_REDIS:
      redis_hash_name = self._GetProcessedRedisHashName(session_identifier)

      try:
        task_identifiers = self._redis_client.hkeys(redis_hash_name)
        task_identifiers = [
            identifier.decode('utf-8') for identifier in task_identifiers]
      except redis.exceptions.TimeoutError:
        # If there is a timeout fetching identifiers, we assume that there are
        # no processed tasks.
        task_identifiers = []

    elif task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      if not self._processed_task_storage_path:
        raise IOError('Missing processed task storage path.')

      task_identifiers = [
          path.replace('.plaso', '')
          for path in os.listdir(self._processed_task_storage_path)]

    return task_identifiers

  def _PrepareMergeTaskStorage(self, task_storage_format, task):
    """Prepares a task storage for merging.

    Moves the task storage file from the processed directory to the merge
    directory.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Raises:
      IOError: if the SQLite task storage file cannot be renamed.
      OSError: if the SQLite task storage file cannot be renamed.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_REDIS:
      # TODO: use number of attribute containers instead of file size?
      task.storage_file_size = 1000

      redis_hash_name = self._GetProcessedRedisHashName(task.session_identifier)
      number_of_results = self._redis_client.hdel(
          redis_hash_name, task.identifier)
      if number_of_results == 0:
        raise IOError('Task identifier {0:s} was not processed'.format(
            task.identifier))

      redis_hash_name = self._GetMergeTaskStorageRedisHashName(task)
      # TODO: set timestamp as value.
      self._redis_client.hset(
          redis_hash_name, key=task.identifier, value=b'true')

    elif task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      merge_storage_file_path = self._GetMergeTaskStorageFilePath(
          task_storage_format, task)
      processed_storage_file_path = self._GetProcessedStorageFilePath(task)

      task.storage_file_size = os.path.getsize(processed_storage_file_path)

      try:
        os.rename(processed_storage_file_path, merge_storage_file_path)
      except OSError as exception:
        raise IOError((
            'Unable to rename task storage file: {0:s} with error: '
            '{1!s}').format(processed_storage_file_path, exception))

  def _RemoveMergeTaskStorage(self, task_storage_format, task):
    """Removes a merge task storage.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Raises:
      IOError: if a SQLite task storage file cannot be removed.
      OSError: if a SQLite task storage file cannot be removed.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_REDIS:
      redis_hash_pattern = '{0:s}-{1:s}-*'.format(
          task.session_identifier, task.identifier)

      for redis_hash_name in self._redis_client.keys(redis_hash_pattern):
        self._redis_client.delete(redis_hash_name)

    elif task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      merge_storage_file_path = self._GetMergeTaskStorageFilePath(
          task_storage_format, task)

      try:
        os.remove(merge_storage_file_path)
      except OSError as exception:
        raise IOError((
            'Unable to remove merge task storage file: {0:s} with error: '
            '{1!s}').format(merge_storage_file_path, exception))

  def _RemoveProcessedTaskStorage(self, task_storage_format, task):
    """Removes a processed task storage.

    Args:
      task_storage_format (str): storage format used to store task results.
      task (Task): task the storage changes are part of.

    Raises:
      IOError: if a SQLite task storage file cannot be removed.
      OSError: if a SQLite task storage file cannot be removed.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_REDIS:
      redis_hash_pattern = '{0:s}-{1:s}-*'.format(
          task.session_identifier, task.identifier)

      for redis_hash_name in self._redis_client.keys(redis_hash_pattern):
        self._redis_client.delete(redis_hash_name)

    elif task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      processed_storage_file_path = self._GetProcessedStorageFilePath(task)

      try:
        os.remove(processed_storage_file_path)
      except OSError as exception:
        raise IOError((
            'Unable to remove processed task storage file: {0:s} with error: '
            '{1!s}').format(processed_storage_file_path, exception))

  def _StartTaskStorage(self, task_storage_format):
    """Starts the task storage.

    Args:
      task_storage_format (str): storage format used to store task results.

    Raises:
      IOError: if the temporary path for the SQLite task storage already exists.
      OSError: if the temporary path for the SQLite task storage already exists.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_REDIS and redis_store:
      url = redis_store.RedisStore.DEFAULT_REDIS_URL
      self._redis_client = redis.from_url(url=url, socket_timeout=60)
      self._redis_client.client_setname('task_engine')

    elif task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      if self._task_storage_path:
        raise IOError('SQLite task storage path already exists.')

      output_directory = os.path.dirname(self._storage_file_path)
      self._task_storage_path = tempfile.mkdtemp(dir=output_directory)

      self._merge_task_storage_path = os.path.join(
          self._task_storage_path, 'merge')
      os.mkdir(self._merge_task_storage_path)

      self._processed_task_storage_path = os.path.join(
          self._task_storage_path, 'processed')
      os.mkdir(self._processed_task_storage_path)

      self._processing_configuration.task_storage_path = self._task_storage_path

  def _StopTaskStorage(
      self, task_storage_format, session_identifier, abort=False):
    """Stops the task storage.

    The results of tasks will be lost on abort.

    Args:
      task_storage_format (str): storage format used to store task results.
      session_identifier (str): the identifier of the session the tasks are
          part of.
      abort (Optional[bool]): True to indicate the stop is issued on abort.
    """
    if task_storage_format == definitions.STORAGE_FORMAT_REDIS:
      redis_hash_pattern = '{0:s}-*'.format(session_identifier)

      for redis_hash_name in self._redis_client.keys(redis_hash_pattern):
        self._redis_client.delete(redis_hash_name)

      self._redis_client = None

    elif task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      if os.path.isdir(self._merge_task_storage_path):
        if abort:
          shutil.rmtree(self._merge_task_storage_path)
        else:
          os.rmdir(self._merge_task_storage_path)

      if os.path.isdir(self._processed_task_storage_path):
        if abort:
          shutil.rmtree(self._processed_task_storage_path)
        else:
          os.rmdir(self._processed_task_storage_path)

      if os.path.isdir(self._task_storage_path):
        if abort:
          shutil.rmtree(self._task_storage_path)
        else:
          os.rmdir(self._task_storage_path)

      self._merge_task_storage_path = None
      self._processed_task_storage_path = None
      self._task_storage_path = None

      self._processing_configuration.task_storage_path = None
