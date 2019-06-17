# -*- coding: utf-8 -*-
"""Reader for SQLite storage files."""

from __future__ import unicode_literals

from plaso.storage import file_interface
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileReader(file_interface.StorageFileReader):
  """SQLite-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(SQLiteStorageFileReader, self).__init__(path)
    self._storage_file = sqlite_file.SQLiteStorageFile()
    self._storage_file.Open(path=path)
