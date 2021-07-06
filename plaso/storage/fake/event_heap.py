# -*- coding: utf-8 -*-
"""Heap to sort events in chronological order."""

import heapq


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
