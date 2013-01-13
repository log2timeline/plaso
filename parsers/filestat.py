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
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import sleuthkit


class PfileStat(parser.PlasoParser):
  """Parse the PFile Stat object to extract filesystem timestamps.."""

  NAME = 'File Stat'
  PARSER_TYPE = 'FILE'

  DATE_MULTIPLIER = 1000000

  def Parse(self, filehandle):
    """Extract the stat object and parse it."""
    stat = filehandle.Stat()

    if not stat:
      return

    times = []
    for item, _ in stat:
      if item[-4:] == 'time':
        times.append(item)

    event_container = event.EventContainer()

    event_container.offset = 0
    event_container.source_short = self.PARSER_TYPE
    event_container.allocated = True

    # Check if file is allocated (only applicable for TSK).
    check_allocated = getattr(filehandle, 'IsAllocated', None)
    if check_allocated and check_allocated():
      event_container.allocated = False

    for time in times:
      evt = event.EventObject()
      evt.timestamp = int(self.DATE_MULTIPLIER * getattr(stat, time, 0))
      evt.timestamp += getattr(stat, '%s_nano' % time, 0)

      if not evt.timestamp:
        continue

      evt.timestamp_desc = time
      evt.source_long = u'%s Time' % getattr(stat, 'os_type', 'N/A')

      event_container.Append(evt)

    return event_container


class PfileStatFormatter(eventdata.EventFormatter):
  """Define the formatting for PFileStat."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('PfileStat:', re.DOTALL)

  # The format string.
  FORMAT_STRING = u'{display_name}{text_append}'
  FORMAT_STRING_SHORT = u'{filename}'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    event_object.text_append = u''

    if not hasattr(event_object, 'allocated'):
      event_object.text_append = u' (unallocated)'

    return super(PfileStatFormatter, self).GetMessages(event_object)
