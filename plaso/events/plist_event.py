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
"""This file is the template for Plist events."""

from plaso.lib import event
from plaso.lib import eventdata


class PlistEvent(event.EventObject):
  """Convenience class for a plist events."""
  DATA_TYPE = 'plist:key'

  def __init__(self, root, key, timestamp, desc=None, host=None, user=None):
    """Initializes a plist event.

    Args:
      root: A string representing the path from the root to this key.
      key: A string representing the name of key.
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      desc: An optional string intended for the user describing the event.
      host: An optional host name if one is available within the log file.
      user: An optional user name if one is available within the log file.
    """
    super(PlistEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.root = root
    self.key = key
    if desc:
      self.desc = desc
    if host:
      self.hostname = host
    if user:
      self.username = user
