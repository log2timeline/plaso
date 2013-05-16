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
"""This file contains a default plist plugin in Plaso."""

import datetime
import logging

from plaso.events import plist_event
from plaso.lib import plist_interface
from plaso.lib import timelib


class DefaultPlugin(plist_interface.PlistPlugin):
  """Basic plugin to extract keys with timestamps as values from plists."""

  def Process(self, plist_name, top_level):
    self._top_level = top_level
    logging.debug(u'Plist {} plugin used for: {}'.format(
        self.plugin_name, plist_name))
    return self.GetEntries()

  def GetEntries(self):
    """Simple method to exact date values from a Plist.

    Yields:
      An EventObject from Plists values that are date objects.
    """
    for root, key, value in plist_interface.RecurseKey(self._top_level):
      if isinstance(value, datetime.datetime):
        time = timelib.Timestamp.FromPosixTime(timelib.Timetuple2Timestamp(
            value.timetuple()))
        yield plist_event.PlistEvent(root, key, time)
      # TODO(make): Binplist keeps a list of offsets but not mapped to a key.
      # adjust code when there is a way to map keys to offsets.

