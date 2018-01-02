# -*- coding: utf-8 -*-
"""Storage writer for SQLite storage files."""

from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage.sqlite import merge_reader
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileWriter(interface.StorageFileWriter):
  """SQLite-based storage file writer."""

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      SQLiteStorageFile: storage file.
    """
    return sqlite_file.SQLiteStorageFile(storage_type=self._storage_type)

  def _CreateTaskStorageMergeReader(self, path):
    """Creates a task storage merge reader.

    Args:
      path (str): path to the task storage file that should be merged.

    Returns:
      SQLiteStorageMergeReader: storage merge reader.
    """
    return merge_reader.SQLiteStorageMergeReader(self, path)

  def _CreateTaskStorageWriter(self, path, task):
    """Creates a task storage writer.

    Args:
      path (str): path to the storage file.
      task (Task): task.

    Returns:
      SQLiteStorageFileWriter: storage writer.
    """
    return SQLiteStorageFileWriter(
        self._session, path,
        storage_type=definitions.STORAGE_TYPE_TASK, task=task)
