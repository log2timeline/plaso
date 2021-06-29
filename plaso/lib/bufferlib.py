# -*- coding: utf-8 -*-
"""Circular buffer for storing event objects."""


class CircularBuffer(object):
  """Class that defines a circular buffer for storing event objects."""

  def __init__(self, size):
    """Initializes a circular buffer object.

    Args:
      size (int): number of elements in the buffer.
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
    """int: number of elements in the buffer."""
    return self._size

  def Append(self, item):
    """Add an item to the list.

    Args:
      item (object): item.
    """
    if self._index >= self._size:
      self._index = self._index % self._size

    try:
      self._list[self._index] = item
    except IndexError:
      self._list.append(item)
    self._index += 1

  def Clear(self):
    """Removes all elements from the list."""
    self._index = 0
    self._list = []

  def Flush(self):
    """Returns a generator for all items and clear the buffer."""
    for item in self:
      yield item
    self.Clear()

  def GetCurrent(self):
    """Retrieves the current item that index points to.

    Return:
      object: item.
    """
    index = self._index - 1
    if index < 0:
      return None

    return self._list[index]
