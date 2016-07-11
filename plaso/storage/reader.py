# -*- coding: utf-8 -*-
"""The storage object reader."""

# TODO: deprecate this class.
class StorageObjectReader(object):
  """Class that implements a storage object reader."""

  def __init__(self, storage_object):
    """Initializes a storage reader object.

    Args:
      storage_object: a ZIP-based storage file (instance of ZIPStorageFile).
    """
    super(StorageObjectReader, self).__init__()
    self._storage_object = storage_object

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self._storage_object.Close()

  def GetEvents(self, time_range=None):
    """Retrieves events.

    Args:
      time_range: an optional time range object (instance of TimeRange).

    Returns:
      A generator of event objects (instances of EventObject).
    """
    return self._storage_object.GetEvents(time_range=time_range)

  def GetEventSources(self):
    """Retrieves event sources.

    Returns:
      A generator of event source objects (instances of EventSourceObject).
    """
    return self._storage_object.GetEventSources()
