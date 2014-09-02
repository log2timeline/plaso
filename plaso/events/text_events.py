#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains the text format specific event object classes."""

from plaso.events import time_events
from plaso.lib import eventdata


class TextEvent(time_events.TimestampEvent):
  """Convenience class for a text format-based event."""

  DATA_TYPE = 'text:entry'

  def __init__(self, timestamp, offset, attributes):
    """Initializes a text event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the attributes.
      attributes: A dict that contains the events attributes.
    """
    super(TextEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.offset = offset

    for name, value in attributes.iteritems():
      # TODO: Revisit this constraints and see if we can implement
      # it using a more sane solution.
      if isinstance(value, basestring) and not value:
        continue
      setattr(self, name, value)
