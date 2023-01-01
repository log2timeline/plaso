# -*- coding: utf-8 -*-
"""Fake (in-memory only) store for testing."""

from acstore import fake_store as acstore_fake_store

from plaso.containers import events
from plaso.storage.fake import event_heap


class FakeStore(acstore_fake_store.FakeAttributeContainerStore):
  """Fake (in-memory only) store for testing.

  Attributes:
    serialization_format (str): serialization format.
  """

  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

  def __init__(self):
    """Initializes a fake (in-memory only) store."""
    super(FakeStore, self).__init__()
    self._serializers_profiler = None
    self.serialization_format = None

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage writer.')

    generator = self.GetAttributeContainers(self._CONTAINER_TYPE_EVENT)
    sorted_events = event_heap.EventHeap()

    for event_index, event in enumerate(generator):
      if (time_range and (
          event.timestamp < time_range.start_timestamp or
          event.timestamp > time_range.end_timestamp)):
        continue

      # The event index is used to ensure to sort events with the same date and
      # time and description in the order they were added to the store.
      sorted_events.PushEvent(event, event_index)

    return iter(sorted_events.PopEvents())

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler
