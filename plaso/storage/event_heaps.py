# -*- coding: utf-8 -*-
"""Heaps to sort events in chronological order."""

from __future__ import unicode_literals

import heapq


# TODO: since this is only used by the fake storage implementation
# move this class into the fake submodule.
class EventHeap(object):
  """Event heap."""

  def __init__(self):
    """Initializes an event heap."""
    super(EventHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      EventObject: event.
    """
    try:
      _, _, _, _, event = heapq.heappop(self._heap)
      return event

    except IndexError:
      return None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      EventObject: event.
    """
    event = self.PopEvent()
    while event:
      yield event
      event = self.PopEvent()

  def PushEvent(self, event, event_index):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
      event_index (int): index of the event in the storage.
    """
    event_string = event.GetAttributeValuesString()
    heap_values = (
        event.timestamp, event.timestamp_desc, event_index, event_string, event)
    heapq.heappush(self._heap, heap_values)


class SerializedEventHeap(object):
  """Serialized event heap.

  Attributes:
    data_size (int): total data size of the serialized events on the heap.
  """

  def __init__(self):
    """Initializes a serialized event heap."""
    super(SerializedEventHeap, self).__init__()
    self._heap = []
    self.data_size = 0

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  def Empty(self):
    """Empties the heap."""
    self._heap = []
    self.data_size = 0

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      tuple: containing:

        int: event timestamp or None if the heap is empty
        bytes: serialized event or None if the heap is empty
    """
    try:
      timestamp, serialized_event = heapq.heappop(self._heap)

      self.data_size -= len(serialized_event)
      return timestamp, serialized_event

    except IndexError:
      return None, None

  def PushEvent(self, timestamp, event_data):
    """Pushes a serialized event onto the heap.

    Args:
      timestamp (int): event timestamp, which contains the number of
          micro seconds since January 1, 1970, 00:00:00 UTC.
      event_data (bytes): serialized event.
    """
    heap_values = (timestamp, event_data)
    heapq.heappush(self._heap, heap_values)
    self.data_size += len(event_data)
