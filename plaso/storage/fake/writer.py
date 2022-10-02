# -*- coding: utf-8 -*-
"""Fake (in-memory only) storage writer for testing."""

from plaso.lib import definitions
from plaso.storage import writer
from plaso.storage.fake import fake_store


class FakeStorageWriter(writer.StorageWriter):
  """Fake (in-memory only) storage writer object.

  Attributes:
    task_completion (TaskCompletion): task completion attribute container.
    task_start (TaskStart): task start attribute container.
  """

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a storage writer object.

    Args:
      storage_type (Optional[str]): storage type.
    """
    super(FakeStorageWriter, self).__init__(storage_type=storage_type)
    self._first_written_event_data_index = 0
    self._first_written_event_source_index = 0
    self._written_event_data_index = 0
    self._written_event_source_index = 0
    self.task_completion = None
    self.task_start = None

  def GetFirstWrittenEventData(self):
    """Retrieves the first event data that was written after open.

    Using GetFirstWrittenEventData and GetNextWrittenEventData newly
    added event data can be retrieved in order of addition.

    Returns:
      EventData: event data or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    event_data = self._store.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_DATA, self._first_written_event_data_index)
    self._written_event_data_index = self._first_written_event_data_index + 1
    return event_data

  def GetNextWrittenEventData(self):
    """Retrieves the next event data that was written after open.

    Returns:
      EventData: event data or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    event_data = self._store.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_DATA, self._written_event_data_index)
    self._written_event_data_index += 1
    return event_data

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
    self._written_event_source_index += 1
    return event_source

  def Open(self, **unused_kwargs):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._store:
      raise IOError('Storage writer already opened.')

    self._store = fake_store.FakeStore()
    self._store.Open()

    self._first_written_event_data_index = 0
    self._first_written_event_source_index = 0
    self._written_event_data_index = 0
    self._written_event_source_index = 0
