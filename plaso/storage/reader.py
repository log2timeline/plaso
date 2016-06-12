# -*- coding: utf-8 -*-
"""The storage object reader."""

from plaso.storage import interface


class StorageObjectReader(interface.StorageReader):
  """Class that implements a storage object reader."""

  def __init__(self, storage_object):
    """Initializes a storage reader object.

    Args:
      storage_object: a ZIP-based storage file (instance of ZIPStorageFile).
    """
    super(StorageObjectReader, self).__init__()
    self._storage_object = storage_object

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self._storage_object.Close()

  def GetEvents(self, time_range=None):
    """Retrieves events.

    Args:
      time_range: an optional time range object (instance of TimeRange).

    Yields:
      Event objects (instances of EventObject).
    """
    event_object = self._storage_object.GetSortedEntry(
        time_range=time_range)

    while event_object:
      yield event_object
      event_object = self._storage_object.GetSortedEntry(
          time_range=time_range)

  def GetEventSources(self):
    """Retrieves event sources.

    Returns:
      A generator of event source objects (instances of EventSourceObject).
    """
    return self._storage_object.GetEventSources()
