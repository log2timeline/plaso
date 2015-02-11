#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from plaso.lib import bufferlib


class TestBuffer(unittest.TestCase):
  """Test the circular buffer."""

  def testBuffer(self):
    items = range(1, 11)

    circular_buffer = bufferlib.CircularBuffer(10)

    self.assertEquals(len(circular_buffer), 10)
    self.assertEquals(circular_buffer.size, 10)
    self.assertTrue(circular_buffer.GetCurrent() is None)

    for item in items:
      circular_buffer.Append(item)
      self.assertEquals(circular_buffer.GetCurrent(), item)
      self.assertEquals(circular_buffer.size, 10)

    content = list(circular_buffer)
    self.assertEquals(items, content)

    circular_buffer.Append(11)
    self.assertEquals(
        [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], list(circular_buffer.Flush()))

    self.assertEquals(circular_buffer.GetCurrent(), None)

    new_items = range(1, 51)
    for item in new_items:
      circular_buffer.Append(item)
      self.assertEquals(circular_buffer.GetCurrent(), item)
      self.assertEquals(circular_buffer.size, 10)

    self.assertEquals(range(41, 51), list(circular_buffer))


if __name__ == '__main__':
  unittest.main()
