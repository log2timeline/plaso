#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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


class PfileStatEventContainer(event.EventContainer):
  """File system stat event container."""

  def __init__(self, allocated):
    """Initializes the event container.

    Args:
      allocated: Boolean value to indicate the file entry is allocated.
    """
    super(PfileStatEventContainer, self).__init__()

    self.data_type = 'fs:stat'

    # TODO: refactor to formatter.
    self.source_short = 'FILE'

    self.offset = 0
    self.allocated = allocated


class PfileStatParser(parser.PlasoParser):
  """Parse the PFile Stat object to extract filesystem timestamps.."""
  NAME = 'File Stat'
  PARSER_TYPE = 'FILE'

  def Parse(self, filehandle):
    """Extract the stat object and parse it."""
    stat = filehandle.Stat()

    if not stat:
      return

    times = []
    for item, _ in stat:
      if item[-4:] == 'time':
        times.append(item)

    # Check if file is allocated (only applicable for TSK).
    # TODO: the logic here is screwed, rename the function to
    # IsUnAllocated() or change return. I opt to flag the unallocated
    # files not allocted.
    is_allocated = True
    check_allocated = getattr(filehandle, 'IsAllocated', None)
    if check_allocated and check_allocated():
      is_allocated = False

    event_container = PfileStatEventContainer(is_allocated)

    for time in times:
      evt = event.EventObject()
      evt.timestamp = timelib.Timestamp.FromPosixTime(getattr(stat, time, 0))
      evt.timestamp += getattr(stat, '%s_nano' % time, 0)

      if not evt.timestamp:
        continue

      evt.timestamp_desc = time
      evt.source_long = u'%s Time' % getattr(stat, 'os_type', 'N/A')

      event_container.Append(evt)

    return event_container

