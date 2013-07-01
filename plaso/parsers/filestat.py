#!/usr/bin/python
# -*- coding: utf-8 -*-
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


def GetEventContainerFromStat(stat, is_allocated=True):
  """Return an EventContainer object from a file stat object.

  This method takes a stat object and creates an EventContainer
  that contains all extracted timestamps from the stat object.

  The constraints are that the stat object implements an iterator
  that returns back values all timestamp based values have the
  attribute name 'time' in them. All timestamps also need to be
  stored as a Posix timestamps.

  Args:
    stat: A stat object, preferably a pfile.Stat object.
    is_allocated: A boolean variable defining if the file is
    currently allocated or not.

  Returns:
    An EventContainer that contains an EventObject for each extracted
    timestamp contained in the stat object.
  """
  times = []
  for item, _ in stat:
    if item[-4:] == 'time':
      times.append(item)

  event_container = PfileStatEventContainer(is_allocated)

  for time in times:
    evt = event.EventObject()
    evt.timestamp = timelib.Timestamp.FromPosixTime(getattr(stat, time, 0))
    evt.timestamp += getattr(stat, '%s_nano' % time, 0)

    if not evt.timestamp:
      continue

    evt.timestamp_desc = time
    evt.fs_type = getattr(stat, 'fs_type', 'N/A')

    event_container.Append(evt)

  return event_container


class PfileStatEventContainer(event.EventContainer):
  """File system stat event container."""

  def __init__(self, allocated):
    """Initializes the event container.

    Args:
      allocated: Boolean value to indicate the file entry is allocated.
    """
    super(PfileStatEventContainer, self).__init__()

    self.data_type = 'fs:stat'

    self.offset = 0
    self.allocated = allocated


class PfileStatParser(parser.PlasoParser):
  """Parse the PFile Stat object to extract filesystem timestamps."""

  def Parse(self, filehandle):
    """Extract the stat object and parse it."""
    stat = filehandle.Stat()

    if not stat:
      return

    allocated = getattr(stat, 'allocated', True)
    return GetEventContainerFromStat(stat, allocated)
