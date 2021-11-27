# -*- coding: utf-8 -*-
"""Storage writer for SQLite storage files."""

from plaso.storage import writer
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileWriter(writer.StorageWriter):
  """SQLite-based storage file writer."""

  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    event_source = self._store.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE,
        self._first_written_event_source_index)

    if event_source:
      self._written_event_source_index = (
          self._first_written_event_source_index + 1)
    return event_source

  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    event_source = self._store.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE, self._written_event_source_index)
    if event_source:
      self._written_event_source_index += 1
    return event_source

  # pylint: disable=arguments-differ
  def Open(self, path=None, **unused_kwargs):
    """Opens the storage writer.

    Args:
      path (Optional[str]): path to the output file.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._store:
      raise IOError('Storage writer already opened.')

    self._store = sqlite_file.SQLiteStorageFile()

    if self._serializers_profiler:
      self._store.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._store.SetStorageProfiler(self._storage_profiler)

    self._store.Open(path=path, read_only=False)

    number_of_event_sources = self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)
    self._first_written_event_source_index = number_of_event_sources
    self._written_event_source_index = self._first_written_event_source_index
