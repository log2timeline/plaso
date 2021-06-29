#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the circular buffer for storing event objects."""

import unittest

from plaso.lib import bufferlib


class CircularBufferTest(unittest.TestCase):
  """Tests for the circular buffer for storing event objects."""

  def testBuffer(self):
    """Tests the circular buffer."""
    items = list(range(1, 11))

    circular_buffer = bufferlib.CircularBuffer(10)

    self.assertEqual(len(circular_buffer), 10)
    self.assertEqual(circular_buffer.size, 10)

    current_item = circular_buffer.GetCurrent()
    self.assertIsNone(current_item)

    for item in items:
      circular_buffer.Append(item)
      current_item = circular_buffer.GetCurrent()
      self.assertEqual(current_item, item)
      self.assertEqual(circular_buffer.size, 10)

    content = list(circular_buffer)
    self.assertEqual(items, content)

    circular_buffer.Append(11)

    expected_items = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    items = list(circular_buffer.Flush())
    self.assertEqual(items, expected_items)

    self.assertIsNone(circular_buffer.GetCurrent())

    items = list(range(1, 51))
    for item in items:
      circular_buffer.Append(item)
      self.assertEqual(circular_buffer.GetCurrent(), item)
      self.assertEqual(circular_buffer.size, 10)

    expected_items = list(range(41, 51))
    items = list(circular_buffer)
    self.assertEqual(items, expected_items)


if __name__ == '__main__':
  unittest.main()
