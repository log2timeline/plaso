from plaso.lib import definitions
from plaso.storage import interface
from sqlite_file import SQLiteStorageFile
from plaso.storage.sqlite.merge_reader import SQLiteStorageMergeReader


class SQLiteStorageFileWriter(interface.StorageFileWriter):
  """SQLite-based storage file writer."""

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      sqlite_file.SQLiteStorageFile: storage file.
    """
    return SQLiteStorageFile(storage_type=self._storage_type)

  def _CreateTaskStorageMergeReader(self, path):
    """Creates a task storage merge reader.

    Args:
      path (str): path to the task storage file that should be merged.

    Returns:
      plaso.storage.sqlite.merge_reader.SQLiteStorageMergeReader: storage merge reader.
    """
    return SQLiteStorageMergeReader(self, path)

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