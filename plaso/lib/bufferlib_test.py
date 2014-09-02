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
"""Tests for plaso.lib.buffer"""

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
