#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""This file contains SELinux log file parser in plaso.

   Information updated 16 january 2013.

   The parser applies to SELinux 'audit.log' file.
   An entry log file example is the following:

   type=AVC msg=audit(1105758604.519:420): avc: denied { getattr } for pid=5962
   comm="httpd" path="/home/auser/public_html" dev=sdb2 ino=921135

   The Parser will extract the 'type' value, the timestamp abd the 'pid'.
   In the previous example, the timestamp is '1105758604.519', and it
   represents the EPOCH time (seconds since Jan 1, 1970) plus the
   milliseconds past current time (epoch: 1105758604, milliseconds: 519).

   The number after the timestamp (420 in the example) is a 'serial number'
   that can be used to correlate multiple logs generated from the same event.

   References
   http://selinuxproject.org/page/NB_AL
   http://blog.commandlinekungfu.com/2010/08/episode-106-epoch-fail.html
   http://www.redhat.com/promo/summit/2010/presentations/
   taste_of_training/Summit_2010_SELinux.pdf
"""

import datetime
import logging
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import lexer
from plaso.lib import parser
from plaso.lib import timelib

__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxLineEvent(event.TextEvent):
  """Convenience class for a SELinux log line event."""
  DATA_TYPE = 'selinux:line'

  def __init__(self, timestamp, offset, attributes):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the event.
      attributes: A dict that contains the events attributes
    """
    super(SELinuxLineEvent, self).__init__(
        timestamp, attributes, 'Audit log File')
    self.offset = offset


class SELinux(parser.TextParser):
  """Parse SELinux audit log files using the TextParser."""

  NAME = 'SELinux'
  SOURCE_LONG = 'Audit log file'
  PID_RE = re.compile('pid=([0-9]+)[\s]+', re.DOTALL)

  tokens = [
    lexer.Token('INITIAL', r'^type=([\w]+)[ \t]+', 'ParseType', 'MSG'),
    lexer.Token('MSG', r'msg=audit\(([0-9]+)\.([0-9]+):[0-9]*\):[ \t]+',
                'ParseTime', 'STRING'),
    lexer.Token('STRING', r'([^\n]+)', 'ParseString', ''),
    lexer.Token('STRING', r'\n', 'ParseMessage', 'INITIAL'),
    lexer.Token('.', '([^\n]+)\n', 'ParseIncomplete', 'INITIAL')
  ]

  def __init__(self, pre_obj):
    """SELinux parser object constructor."""
    # Set local_zone to false, since timestamps are UTC.
    super(SELinux, self).__init__(pre_obj, False)
    self.attributes = {'audit_type': '', 'pid': '', 'body': ''}
    self.timestamp = 0

  def ParseType(self, match, **_):
    """Parse the audit event type."""
    self.attributes['audit_type'] = match.group(1)

  def ParseTime(self, match, **_):
    """Parse the log timestamp."""
    try:
      self.timestamp = timelib.Timestamp.FromPosixTime(
        int(match.group(1))) + (int(match.group(2))*1000)
    except ValueError as e:
      logging.error(('Error %s, unable to get UTC timestamp', e))
      self.timestamp = 0

  def ParseString(self, match, **_):
    """Add a string to the body attribute.

    This method extends the one from TextParser slightly,
    searching for the 'pid=[0-9]+' value inside the message body.

    """
    try:
      self.attributes['body'] += match.group(1).strip('\n')
      # TODO: fix it using lexer or remove pid parsing.
      pid_search = self.PID_RE.search(self.attributes['body'])
      if pid_search:
        self.attributes['pid'] = pid_search.group(1)
    except IndexError:
      self.attributes['body'] += match.group(0).strip('\n')

  def ParseLine(self, zone):
    """Parse a single line from the SELinux audit file.

    This method extends the one from TextParser slightly, creating a 
    TextEvent with the timestamp (UTC) taken from log entries.

    Args:
      zone: The timezone of the host computer, not used since the
      timestamp are UTC.

    Returns:
      An EventObject that is constructed from the selinux entry.
    """
    offset = getattr(self, 'entry_offset', 0)
    evt = SELinuxLineEvent(self.timestamp, offset, self.attributes)
    self.timestamp = 0
    return evt
