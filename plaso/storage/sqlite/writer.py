# -*- coding: utf-8 -*-
"""Storage writer for SQLite storage files."""

from plaso.lib import definitions
from plaso.storage import writer
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileWriter(writer.StorageWriter):
  """SQLite-based storage file writer."""

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
    self._store.AddEventTag(event_tag)

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

    self._store = sqlite_file.SQLiteStorageFile(storage_type=self._storage_type)

    if self._serializers_profiler:
      self._store.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._store.SetStorageProfiler(self._storage_profiler)

    self._store.Open(path=path, read_only=False)

    number_of_event_sources = self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)
    self._first_written_event_source_index = number_of_event_sources
    self._written_event_source_index = self._first_written_event_source_index

  def WriteSessionCompletion(self, session):
    """Writes session completion information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    session_completion = session.CreateSessionCompletion()
    self._store.WriteSessionCompletion(session_completion)

  def WriteSessionConfiguration(self, session):
    """Writes session configuration information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
      OSError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session configuration not supported by storage type.')

    session_configuration = session.CreateSessionConfiguration()
    self._store.WriteSessionConfiguration(session_configuration)

  def WriteSessionStart(self, session):
    """Writes session start information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    session_start = session.CreateSessionStart()
    self._store.WriteSessionStart(session_start)
