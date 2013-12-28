#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a parser for the Stat object of a PFile."""

from plaso.lib import event
from plaso.lib import parser
from plaso.lib import timelib


# TODO: move this function to lib or equiv since it is used from the collector
# as well.


def GetEventContainerFromStat(stat_object):
  """Return an EventContainer object from a file stat object.

  This method takes a stat object and creates an EventContainer
  that contains all extracted timestamps from the stat object.

  The constraints are that the stat object implements an iterator
  that returns back values all timestamp based values have the
  attribute name 'time' in them. All timestamps also need to be
  stored as a Posix timestamps.

  Args:
    stat_object: A stat object.

  Returns:
    An EventContainer that contains an EventObject for each extracted
    timestamp contained in the stat object or None if the stat object
    does not contain time values.
  """
  # TODO: this is highly fragile improve this solution.
  time_values = []
  for item, _ in stat_object:
    if item[-4:] == 'time':
      time_values.append(item)

  if not time_values:
    return

  is_allocated = getattr(stat_object, 'allocated', True)

  event_container = PfileStatEventContainer(
      is_allocated, stat_object.attributes.get('size', None))

  for time_value in time_values:
    timestamp = getattr(stat_object, time_value, 0)
    event_object = event.EventObject()
    event_object.timestamp = timelib.Timestamp.FromPosixTime(timestamp)
    event_object.timestamp += getattr(stat_object, '%s_nano' % time_value, 0)

    if not event_object.timestamp:
      continue

    event_object.timestamp_desc = time_value
    event_object.fs_type = getattr(stat_object, 'fs_type', 'N/A')

    event_container.Append(event_object)

  return event_container


class PfileStatEventContainer(event.EventContainer):
  """File system stat event container."""

  def __init__(self, allocated, size):
    """Initializes the event container.

    Args:
      allocated: Boolean value to indicate the file entry is allocated.
      size: The file size in bytes.
    """
    super(PfileStatEventContainer, self).__init__()

    self.data_type = 'fs:stat'

    self.offset = 0
    self.size = size
    self.allocated = allocated


class PfileStatParser(parser.BaseParser):
  """Parse the PFile Stat object to extract filesystem timestamps."""

  NAME = 'filestat'

  def Parse(self, file_entry):
    """Extract data from a file system stat entry.

    Args:
      file_entry: A file entry object.

    Yields:
      An event container (EventContainer) that contains the parsed
      attributes.
    """
    stat_object = file_entry.Stat()

    if stat_object:
      event_container = GetEventContainerFromStat(stat_object)
      if event_container:
        yield event_container
