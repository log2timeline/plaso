#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for the range list."""

import unittest

from plaso.classifier import range_list


class RangeListTest(unittest.TestCase):
  """Class to test the range list."""

  def testInsertPositiveRanges(self):
    """Function to test the insert function using positive ranges."""
    range_list_object = range_list.RangeList()

    # Test non-overlapping range.
    range_list_object.Insert(500, 100)
    self.assertEquals(range_list_object.number_of_ranges, 1)

    range_object = range_list_object.ranges[0]
    self.assertEquals(range_object.start_offset, 500)
    self.assertEquals(range_object.end_offset, 600)
    self.assertEquals(range_object.size, 100)

    # Test non-overlapping range.
    range_list_object.Insert(2000, 100)
    self.assertEquals(range_list_object.number_of_ranges, 2)

    range_object = range_list_object.ranges[1]
    self.assertEquals(range_object.start_offset, 2000)
    self.assertEquals(range_object.end_offset, 2100)
    self.assertEquals(range_object.size, 100)

    # Test range that overlaps with an existing range at the start.
    range_list_object.Insert(1950, 100)
    self.assertEquals(range_list_object.number_of_ranges, 2)

    range_object = range_list_object.ranges[1]
    self.assertEquals(range_object.start_offset, 1950)
    self.assertEquals(range_object.end_offset, 2100)
    self.assertEquals(range_object.size, 150)

    # Test range that overlaps with an existing range at the end.
    range_list_object.Insert(2050, 100)
    self.assertEquals(range_list_object.number_of_ranges, 2)

    range_object = range_list_object.ranges[1]
    self.assertEquals(range_object.start_offset, 1950)
    self.assertEquals(range_object.end_offset, 2150)
    self.assertEquals(range_object.size, 200)

    # Test non-overlapping range.
    range_list_object.Insert(1000, 100)
    self.assertEquals(range_list_object.number_of_ranges, 3)

    range_object = range_list_object.ranges[1]
    self.assertEquals(range_object.start_offset, 1000)
    self.assertEquals(range_object.end_offset, 1100)
    self.assertEquals(range_object.size, 100)

    # Test range that aligns with an existing range at the end.
    range_list_object.Insert(1100, 100)
    self.assertEquals(range_list_object.number_of_ranges, 3)

    range_object = range_list_object.ranges[1]
    self.assertEquals(range_object.start_offset, 1000)
    self.assertEquals(range_object.end_offset, 1200)
    self.assertEquals(range_object.size, 200)

    # Test range that aligns with an existing range at the start.
    range_list_object.Insert(900, 100)
    self.assertEquals(range_list_object.number_of_ranges, 3)

    range_object = range_list_object.ranges[1]
    self.assertEquals(range_object.start_offset, 900)
    self.assertEquals(range_object.end_offset, 1200)
    self.assertEquals(range_object.size, 300)

    # Test non-overlapping range.
    range_list_object.Insert(0, 100)
    self.assertEquals(range_list_object.number_of_ranges, 4)

    range_object = range_list_object.ranges[0]
    self.assertEquals(range_object.start_offset, 0)
    self.assertEquals(range_object.end_offset, 100)
    self.assertEquals(range_object.size, 100)

    # Test invalid ranges.
    with self.assertRaises(ValueError):
      range_list_object.Insert(-1, 100)

    with self.assertRaises(ValueError):
      range_list_object.Insert(3000, -100)


if __name__ == '__main__':
  unittest.main()
