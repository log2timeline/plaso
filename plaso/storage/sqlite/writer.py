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

  # TODO: remove after refactoring.
  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    # TODO: refactor to use AddOrUpdateAttributeContainer
    self._storage_file.AddEventTag(event_tag)

    self._UpdateEventLabelsSessionCounter(event_tag)
