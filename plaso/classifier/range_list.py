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
"""The range list data type."""


class Range(object):
  """Class that implements a range object."""

  def __init__(self, range_offset, range_size):
    """Initializes the range object.

    Args:
      range_offset: the range offset.
      range_size: the range size.

    Raises:
      ValueError: if the range offset or range size is not valid.
    """
    if range_offset < 0:
      raise ValueError(u'Invalid range offset value.')

    if range_size < 0:
      raise ValueError(u'Invalid range size value.')

    super(Range, self).__init__()
    self.start_offset = range_offset
    self.size = range_size
    self.end_offset = range_offset + range_size


class RangeList(object):
  """Class that implements a range list object."""

  def __init__(self):
    """Initializes the range list object."""
    super(RangeList, self).__init__()
    self.ranges = []

  @property
  def number_of_ranges(self):
    """The number of ranges."""
    return len(self.ranges)

  def GetSpanningRange(self):
    """Retrieves the range spanning the entire range list."""
    if self.number_of_ranges == 0:
      return

    first_range = self.ranges[0]
    last_range = self.ranges[-1]
    range_size = last_range.end_offset - first_range.start_offset

    return Range(first_range.start_offset, range_size)

  def Insert(self, range_offset, range_size):
    """Inserts the range defined by the offset and size in the list.

       Note that overlapping ranges will be merged.

    Args:
      range_offset: the range offset.
      range_size: the range size.

    Raises:
      RuntimeError: if the range cannot be inserted.
      ValueError: if the range offset or range size is not valid.
    """
    if range_offset < 0:
      raise ValueError(u'Invalid range offset value.')

    if range_size < 0:
      raise ValueError(u'Invalid range size value.')

    insert_index = None
    merge_index = None

    number_of_range_objects = len(self.ranges)

    range_end_offset = range_offset + range_size

    if number_of_range_objects == 0:
      insert_index = 0

    else:
      range_object_index = 0

      for range_object in self.ranges:
        # Ignore negative ranges.
        if range_object.start_offset < 0:
          range_object_index += 1
          continue

        # Insert the range before an existing one.
        if range_end_offset < range_object.start_offset:
          insert_index = range_object_index
          break

        # Ignore the range since the existing one overlaps it.
        if (range_offset >= range_object.start_offset and
            range_end_offset <= range_object.end_offset):
          break

        # Merge the range since it overlaps the existing one at the end.
        if (range_offset >= range_object.start_offset and
            range_offset <= range_object.end_offset):
          merge_index = range_object_index
          break

        # Merge the range since it overlaps the existing one at the start.
        if (range_end_offset >= range_object.start_offset and
            range_end_offset <= range_object.end_offset):
          merge_index = range_object_index
          break

        # Merge the range since it overlaps the existing one.
        if (range_offset <= range_object.start_offset and
            range_end_offset >= range_object.end_offset):
          merge_index = range_object_index
          break

        range_object_index += 1

      # Insert the range after the last one.
      if range_object_index >= number_of_range_objects:
        insert_index = number_of_range_objects

    if insert_index is not None and merge_index is not None:
      raise RuntimeError(
          u'Unable to insert the range both insert and merge specified.')

    if insert_index is not None:
      self.ranges.insert(insert_index, Range(range_offset, range_size))

    elif merge_index is not None:
      range_object = self.ranges[merge_index]
      if range_offset < range_object.start_offset:
        range_object.size += range_object.start_offset - range_offset
        range_object.start_offset = range_offset
      if range_end_offset > range_object.end_offset:
        range_object.size += range_end_offset - range_object.end_offset
        range_object.end_offset = range_end_offset
