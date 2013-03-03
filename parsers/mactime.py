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
"""Parser for the Sleuthkit (TSK) bodyfile or mactime format.

The format specifications can be read here:
  http://wiki.sleuthkit.org/index.php?title=Body_file
"""
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


class MactimeEvent(event.PosixTimeEvent):
  """Convenience class for a mactime-based event."""

  def __init__(self, posix_time, usage):
    """Initializes a mactime-based event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
    """
    super(MactimeEvent, self).__init__(posix_time, usage, 'mactime:line')


class MactimeParser(parser.TextCSVParser):
  """Parses TSK's mactime bodyfiles."""

  NAME = 'MactimeParser'
  PARSER_TYPE = 'LOG'

  COLUMNS = [
      'md5', 'name', 'inode', 'mode_as_string', 'uid', 'gid', 'size',
      'atime', 'mtime', 'ctime', 'crtime']
  VALUE_SEPARATOR = '|'

  MD5_RE = re.compile('^[0-9a-fA-F]+$')

  _TIMESTAMP_DESC_MAP = {
      'atime': eventdata.EventTimestamp.ACCESS_TIME,
      'crtime': eventdata.EventTimestamp.CREATION_TIME,
      'ctime': eventdata.EventTimestamp.CHANGE_TIME,
      'mtime': eventdata.EventTimestamp.MODIFICATION_TIME,
  }

  def VerifyRow(self, row):
    """Verify we are dealing with a mactime bodyfile."""
    if not self.MD5_RE.match(row['md5']):
      return False

    try:
      if str(int(row['size'])) != row['size']:
        return False
    except ValueError:
      return False

    return True

  def ParseRow(self, row):
    """Parse a single row and return an extracted EventObject from it."""

    container = event.EventContainer()
    container.source_long = 'Mactime Bodyfile'
    container.source_short = 'FILE'

    for key, value in row.items():
      if key == 'md5' and value == '0':
        continue
      if key not in ('atime', 'mtime', 'ctime', 'crtime'):
        setattr(container, key, value)
      # TODO: Refactor into a helper so this can be used by other
      # modules as well.
      if key == 'uid':
        setattr(container, 'username', value)
        if hasattr(self._pre_obj, 'users'):
          for user in self._pre_obj.users:
            if user.get('sid', '') == value:
              container.username = user.get('name', 'N/A')
            if user.get('uid', '') == value:
              container.username = user.get('name', 'N/A')

    for key in ('atime', 'mtime', 'ctime', 'crtime'):
      value = row.get(key, 0)
      if value:
        container.Append(MactimeEvent(
            int(value), self._TIMESTAMP_DESC_MAP[key]))

    if len(container) > 0:
      return container

