# -*- coding: utf-8 -*-


class CircularBuffer(object):
  """Simple circular buffer for storing EventObjects."""

  def __init__(self, size):
    """Initialize a fixed size circular buffer.

    Args:
      size: An integer indicating the number of elements in the buffer.
    """
    self._size = size
    self._index = 0
    self._list = []

  def __len__(self):
    """Return the length (the fixed size)."""
    return self._size

  @property
  def size(self):
    return self._size

  def GetCurrent(self):
    """Return the current item that index points to."""
    index = self._index - 1
    if index < 0:
      return

    return self._list[index]

  def Clear(self):
    """Clear all elements in the list."""
    self._list = []
    self._index = 0

  def __iter__(self):
    """Return all elements from the list."""
    for index in range(0, self._size):
      try:
        yield self._list[(self._index + index) % self._size]
      except IndexError:
        pass

  def Flush(self):
    """Return a generator for all items and clear the buffer."""
    for item in self:
      yield item
    self.Clear()

  def Append(self, item):
    """Add an item to the list."""
    if self._index >= self._size:
      self._index = self._index % self._size

    try:
      self._list[self._index] = item
    except IndexError:
      self._list.append(item)
    self._index += 1
