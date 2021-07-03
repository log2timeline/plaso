# -*- coding: utf-8 -*-
"""SQLite-based storage file reader."""

from plaso.storage import reader
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileReader(reader.StorageReader):
  """SQLite-based storage file reader."""

  def __init__(self, path):
    """Initializes a SQLite-based file storage reader.

    Args:
      path (str): path to the input file.
    """
    super(SQLiteStorageFileReader, self).__init__()
    self._path = path
    self._store = sqlite_file.SQLiteStorageFile()
    self._store.Open(path=path)
