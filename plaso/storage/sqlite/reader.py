# -*- coding: utf-8 -*-
"""Reader for SQLite storage files."""

from plaso.storage import reader
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileReader(reader.StorageReader):
  """SQLite-based storage file reader."""

  def __init__(self, path):
    """Initializes a SQLite file storage reader.

    Args:
      path (str): path to the input file.
    """
    super(SQLiteStorageFileReader, self).__init__()
    self._path = path
    self._store = sqlite_file.SQLiteStorageFile()
    self._store.Open(path=path)

  def GetFormatVersion(self):
    """Retrieves the format version of the underlying storage file.

    Returns:
      int: the format version, or None if not available.
    """
    if self._store:
      return self._store.format_version

    return None

  def GetSerializationFormat(self):
    """Retrieves the serialization format of the underlying storage file.

    Returns:
      str: the serialization format, or None if not available.
    """
    if self._store:
      return self._store.serialization_format

    return None

  def GetStorageType(self):
    """Retrieves the storage type of the underlying storage file.

    Returns:
      str: the storage type, or None if not available.
    """
    if self._store:
      return self._store.storage_type

    return None
