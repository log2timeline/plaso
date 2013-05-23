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
"""This file contains a formatter for the Stat object of a PFile."""
from plaso.lib import eventdata


class PfileStatFormatter(eventdata.ConditionalEventFormatter):
  """Define the formatting for PFileStat."""
  DATA_TYPE = 'fs:stat'

  FORMAT_STRING_PIECES = [u'{display_name}',
                          u'({unallocated})']
  FORMAT_STRING_SHORT_PIECES = [u'{filename}']

  SOURCE_SHORT = 'FILE'

  def GetSources(self, event_object):
    """Return a list of source short and long messages."""
    self.source_string = u'{} {}'.format(
        getattr(event_object, 'fs_type', 'Unknown'),
        getattr(event_object, 'timestamp_desc', 'Time'))

    return super(PfileStatFormatter, self).GetSources(event_object)

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    if event_object.allocated:
      event_object.unallocated = u'unallocated'

    return super(PfileStatFormatter, self).GetMessages(event_object)
