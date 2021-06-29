# -*- coding: utf-8 -*-
"""Storage writer for SQLite storage files."""

from plaso.storage import file_interface
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileWriter(file_interface.StorageFileWriter):
  """SQLite-based storage file writer."""

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      SQLiteStorageFile: storage file.
    """
    return sqlite_file.SQLiteStorageFile(storage_type=self._storage_type)
