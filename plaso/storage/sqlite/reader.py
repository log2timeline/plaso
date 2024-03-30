# -*- coding: utf-8 -*-
"""SQLite-based storage reader."""

from plaso.storage import reader
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageReader(reader.StorageReader):
  """SQLite-based storage reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input SQLite database.
    """
    super(SQLiteStorageReader, self).__init__()
    self._path = path
    self._store = sqlite_file.SQLiteStorageFile()
    self._store.Open(path=path)
