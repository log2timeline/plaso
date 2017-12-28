# -*- coding: utf-8 -*-
"""Heaps to sort events in chronological order."""

from __future__ import unicode_literals

import abc
import heapq


class BaseEventHeap(object):
  """Event heap interface."""

  def __init__(self):
    """Initializes an event heap."""
    super(BaseEventHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  @abc.abstractmethod
  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      EventObject: event.
    """

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      EventObject: event.
    """
    event = self.PopEvent()
    while event:
      yield event
      event = self.PopEvent()

  @abc.abstractmethod
  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """

  def PushEvents(self, events):
    """Pushes events onto the heap.

    Args:
      events list[EventObject]: events.
    """
    for event in events:
      self.PushEvent(event)


class EventHeap(BaseEventHeap):
  """Event heap."""

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      EventObject: event.
    """
    try:
      _, _, _, event = heapq.heappop(self._heap)
      return event

    except IndexError:
      return None

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    event_string = event.GetAttributeValuesString()
    heap_values = (event.timestamp, event.timestamp_desc, event_string, event)
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
      tuple: contains:

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


class SerializedStreamEventHeap(object):
  """Event heap for serialized stream storage.

  This event heap is used to sort events from multiple streams.
  """

  def __init__(self):
    """Initializes an event heap."""
    super(SerializedStreamEventHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  def PeekEvent(self):
    """Retrieves the first event from the heap without removing it.

    Returns:
      tuple: contains:

        EventObject: event or None.
        int: number of the stream or None.
    """
    try:
      _, stream_number, _, event = self._heap[0]
      return event, stream_number

    except IndexError:
      return None, None

  def PopEvent(self):
    """Retrieves and removes the first event from the heap.

    Returns:
      tuple: contains:

        EventObject: event or None.
        int: number of the stream or None.
    """
    try:
      _, stream_number, _, event = heapq.heappop(self._heap)
      return event, stream_number

    except IndexError:
      return None, None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      tuple: contains:

        EventObject: event or None.
        int: number of the stream or None.
    """
    event, stream_number = self.PopEvent()
    while event:
      yield event, stream_number
      event, stream_number = self.PopEvent()

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    event_identifier = event.GetIdentifier()
    heap_values = (
        event.timestamp, event_identifier.stream_number,
        event_identifier.entry_index, event)
    heapq.heappush(self._heap, heap_values)

  def PushEvents(self, events):
    """Pushes events onto the heap.

    Args:
      events list[EventObject]: events.
    """
    for event in events:
      self.PushEvent(event)
