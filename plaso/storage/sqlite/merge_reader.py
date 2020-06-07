# -*- coding: utf-8 -*-
"""Merge reader for SQLite storage files."""

from __future__ import unicode_literals

import os

from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageMergeReader(interface.StorageMergeReader):
  """SQLite-based storage file reader for merging."""

  def __init__(self, storage_writer, path):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      path (str): path to the input file.
    """
    super(SQLiteStorageMergeReader, self).__init__(storage_writer)
    self._path = path

  def _Close(self):
    """Closes the SQLite task storage file after reading."""
    self._task_store.Close()
    self._task_store = None

    os.remove(self._path)

  def _Open(self):
    """Opens the SQLite task storage file for reading."""
    self._task_store = sqlite_file.SQLiteStorageFile(
        storage_type=definitions.STORAGE_TYPE_TASK)
    self._task_store.Open(self._path)

    table_names = self._task_store.GetTableNames()

    self._container_types = [
        table_name for table_name in self._CONTAINER_TYPES
        if table_name in table_names]
