#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Parser for the Sleuthkit (TSK) bodyfile or mactime format.

The format specifications can be read here:
  http://wiki.sleuthkit.org/index.php?title=Body_file
"""

import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import text_parser


class MactimeEvent(event.PosixTimeEvent):
  """Convenience class for a mactime-based event."""

  DATA_TYPE = 'fs:mactime:line'

  def __init__(self, posix_time, usage, data):
    """Initializes a mactime-based event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      data: A dict object containing extracted data from the body file.
    """
    super(MactimeEvent, self).__init__(posix_time, usage)
    self.user_sid = unicode(data.get('uid', u''))
    self.user_gid = data.get('gid', None)
    self.md5 = data.get('md5', None)
    self.filename = data.get('name', 'N/A')
    self.mode_as_string = data.get('mode_as_string', None)
    self.size = data.get('size', None)

    inode_number = data.get('inode', 0)
    if isinstance(inode_number, basestring):
      if '-' in inode_number:
        inode_number, _, _ = inode_number.partition('-')

      try:
        inode_number = int(inode_number, 10)
      except ValueError:
        inode_number = 0

    self.inode = inode_number


class MactimeParser(text_parser.TextCSVParser):
  """Parses TSK's mactime bodyfiles."""

  NAME = 'mactime'

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
      # Verify that the "size" field is an integer, thus cast it to int
      # and then back to string so it can be compared, if the value is
      # not a string representation of an integer, eg: '12a' then this
      # conversion will fail and we return a False value.
      if str(int(row.get('size', '0'), 10)) != row.get('size', None):
        return False
    except ValueError:
      return False

    # TODO: Add additional verification.
    return True

  def ParseRow(self, row):
    """Parse a single row and yield extracted EventObjects from it."""
    for key, value in row.iteritems():
      try:
        row[key] = int(value, 10)
      except ValueError:
        pass

    for key, timestamp_description in self._TIMESTAMP_DESC_MAP.iteritems():
      value = row.get(key, None)
      if not value:
        continue
      yield MactimeEvent(
          value, timestamp_description, row)
