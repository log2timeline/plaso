#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains buffer related objects used in plaso."""


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
