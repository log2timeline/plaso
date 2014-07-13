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
"""This file contains the shell item specific event object classes."""

from plaso.events import time_events


class ShellItemFileEntryEvent(time_events.FatDateTimeEvent):
  """Convenience class for a shell item file entry event."""

  DATA_TYPE = 'windows:shell_item:file_entry'

  def __init__(
      self, fat_date_time, usage, name, long_name, localized_name, origin):
    """Initializes an event object.

    Args:
      fat_date_time: The FAT date time value.
      usage: The description of the usage of the time value.
      name: A string containing the name of the file entry shell item.
      long_name: A string containing the long name of the file entry shell item.
      localized_name: A string containing the localized name of the file entry
                      shell item.
      origin: A string containing the origin of the event (event source).
    """
    super(ShellItemFileEntryEvent, self).__init__(fat_date_time, usage)

    self.name = name
    self.long_name = long_name
    self.localized_name = localized_name
    self.origin = origin
