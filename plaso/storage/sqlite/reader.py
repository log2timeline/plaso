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
        super().__init__()
        self._path = path
        self._store = sqlite_file.SQLiteStorageFile()
        self._store.Open(path=path)

    def GetAttributeContainersWithStoredData(self, container_type):
        """Retrieves a specific type of attribute containers and their stored data.

        The stored data is the data of an attribute container as stored in the
        underlying store, which can be added as-is to another store, see
        StorageWriter.AddAttributeContainerWithStoredData().

        Args:
          container_type (str): attribute container type.

        Returns:
          generator(tuple[AttributeContainer, object]): attribute container and its
              stored data or None if not available generator.
        """
        return self._store.GetAttributeContainersWithStoredData(container_type)

    def GetCompressionFormat(self):
        """Retrieves the compression format of the stored data.

        Returns:
          str: compression format or None if not available.
        """
        return self._store.compression_format
