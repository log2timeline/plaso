from plaso.storage import interface
from sqlite_file import SQLiteStorageFile


class SQLiteStorageFileReader(interface.StorageFileReader):
  """SQLite-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(SQLiteStorageFileReader, self).__init__(path)
    self._storage_file = SQLiteStorageFile()
    self._storage_file.Open(path=path)