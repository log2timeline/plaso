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

    def PrefetchAttributeContainers(self, container_type, identifiers):
        """Reads specific attribute containers into the read cache.

        Args:
          container_type (str): attribute container type.
          identifiers (list[AttributeContainerIdentifier]): attribute container
              identifiers.
        """
        indexes = [identifier.sequence_number - 1 for identifier in identifiers]
        self._store.PrefetchAttributeContainers(container_type, indexes)
