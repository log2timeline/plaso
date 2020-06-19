# -*- coding: utf-8 -*-
"""Storage writer for SQLite storage files."""

import os

from plaso.lib import definitions
from plaso.storage import file_interface
from plaso.storage.sqlite import merge_reader
from plaso.storage.sqlite import sqlite_file
from plaso.storage.redis import merge_reader as redis_merge_reader
from plaso.storage.redis import writer as redis_writer
from plaso.storage.redis import reader as redis_reader


class SQLiteStorageFileWriter(file_interface.StorageFileWriter):
  """SQLite-based storage file writer."""

  def CreateTaskStorage(self, task, task_storage_format):
    """Creates a task storage.

    The task storage is used to store attribute containers created by the task.

    Args:
      task (Task): task.
      task_storage_format (str): storage format used to store task results.

    Returns:
      StorageWriter: storage writer.

    Raises:
      OSError: if the storage type or storage format is not supported.
      IOError: if the storage type or storage format is not supported.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type: {0:s}'.format(
          self._storage_type))

    if task_storage_format == definitions.STORAGE_FORMAT_SQLITE:
      writer = self._CreateTaskStorageWriter(task)

    elif task_storage_format == definitions.STORAGE_FORMAT_REDIS:
      writer = redis_writer.RedisStorageWriter(
          self._session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    else:
      raise IOError('Unsupported storage format: {0:s}'.format(
          task_storage_format))

    task.storage_format = task_storage_format

    return writer

  def CheckTaskReadyForMerge(self, task):
    """Checks if a task is ready for merging with this session storage.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task is ready to be merged.

    Raises:
      IOError: if the storage type is not supported or
          if the temporary path for the task storage does not exist.
      OSError: if the storage type is not supported or
          if the temporary path for the task storage does not exist.
    """
    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    if not self._processed_task_storage_path:
      raise IOError('Missing processed task storage path.')

    if task.storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return self._CheckSQLiteTaskStoreReadyForMerge(task)

    if task.storage_format == definitions.STORAGE_FORMAT_REDIS:
      return self._CheckRedisTaskStoreReadyForMerge(task)

    raise IOError(
        'Unsupported storage format: {0:s}'.format(task.storage_format))

  def _CheckRedisTaskStoreReadyForMerge(self, task):
    """Checks if a Redis task is ready for merging with this session storage.

    If the task is ready to be merged, this method also sets the task's
    storage file size.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task is ready to be merged.
    """
    reader = redis_reader.RedisStorageReader(task)
    reader.Open()
    is_ready = reader.IsFinalized()
    reader.Close()
    task.storage_file_size = 1000
    return is_ready

  def _CheckSQLiteTaskStoreReadyForMerge(self, task):
    """Checks if a SQLite task is ready for merging with this session storage.

    If the task is ready to be merged, this method also sets the task's
    storage file size.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task is ready to be merged.
    """
    processed_storage_file_path = self._GetProcessedStorageFilePath(task)

    try:
      stat_info = os.stat(processed_storage_file_path)
    except (IOError, OSError):
      return False

    task.storage_file_size = stat_info.st_size
    return True

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      SQLiteStorageFile: storage file.
    """
    return sqlite_file.SQLiteStorageFile(storage_type=self._storage_type)

  def _CreateTaskStorageMergeReader(self, task):
    """Creates a task storage merge reader.

    Args:
     task (Task): task.

    Returns:
      StorageMergeReader: storage merge reader.
    """
    if task.storage_format == definitions.STORAGE_FORMAT_REDIS:
      task_merge_reader = redis_merge_reader.RedisMergeReader(self, task)
    else:
      path = self._GetMergeTaskStorageFilePath(task)
      task_merge_reader = merge_reader.SQLiteStorageMergeReader(self, path)

    task_merge_reader.SetStorageProfiler(self._storage_profiler)
    return task_merge_reader

  def _CreateTaskStorageWriter(self, task):
    """Creates a task storage writer.

    Args:
      task (Task): task.

    Returns:
      SQLiteStorageFileWriter: storage writer.
    """
    storage_file_path = self._GetTaskStorageFilePath(task)
    task_storage_writer = SQLiteStorageFileWriter(
        self._session, storage_file_path,
        storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    task_storage_writer.SetStorageProfiler(self._storage_profiler)
    return task_storage_writer
