# -*- coding: utf-8 -*-
"""Circular buffer for storing event object."""


class CircularBuffer(object):
  """Class that defines a circular buffer for storing event objects."""

  def __init__(self, size):
    """Initializes a circular buffer object.

    Args:
      size: an integer containing the number of elements in the buffer.
    """
    super(CircularBuffer, self).__init__()
    self._index = 0
    self._list = []
    self._size = size

  def __iter__(self):
    """Return all elements from the list."""
    for index in range(0, self._size):
      try:
        yield self._list[(self._index + index) % self._size]
      except IndexError:
        pass

  def __len__(self):
    """Return the length (the fixed size)."""
    return self._size

  @property
  def size(self):
    """The number of elements in the buffer."""
    return self._size

  def Append(self, item):
    """Add an item to the list."""
    if self._index >= self._size:
      self._index = self._index % self._size

    try:
      self._list[self._index] = item
    except IndexError:
      self._list.append(item)
    self._index += 1

  def Clear(self):
    """Clear all elements in the list."""
    self._list = []
    self._index = 0

  def Flush(self):
    """Return a generator for all items and clear the buffer."""
    for item in self:
      yield item
    self.Clear()

  def GetCurrent(self):
    """Return the current item that index points to."""
    index = self._index - 1
    if index < 0:
      return

    return self._list[index]
