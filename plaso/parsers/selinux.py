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

import logging
import re

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import timelib
from plaso.parsers import text_parser


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
    super(SELinuxLineEvent, self).__init__(timestamp, attributes)
    self.offset = offset


class SELinuxParser(text_parser.SlowLexicalTextParser):
  """Parse SELinux audit log files."""

  NAME = 'selinux'

  PID_RE = re.compile(r'pid=([0-9]+)[\s]+', re.DOTALL)

  tokens = [
    # Skipping empty lines, both EOLs are considered here and in other states.
    lexer.Token('INITIAL', r'^\r?\n', '', ''),
    # FSM entry point ('type=anything msg=audit'), critical to recognize a
    # SELinux audit file and used to retrieve the audit type. From there two
    # next states are possible: TIME or failure, since TIME state is required.
    # An empty type is not accepted and it will cause a failure.
    # Examples:
    #   type=SYSCALL msg=audit(...): ...
    #   type=UNKNOWN[1323] msg=audit(...): ...
    lexer.Token('INITIAL', r'^type=([\w]+(\[[0-9]+\])?)[ \t]+msg=audit',
                'ParseType', 'TIMESTAMP'),
    lexer.Token('TIMESTAMP', r'\(([0-9]+)\.([0-9]+):([0-9]*)\):',
                'ParseTime', 'STRING'),
    # Get the log entry description and stay in the same state.
    lexer.Token('STRING', r'[ \t]*([^\r\n]+)', 'ParseString', ''),
    # Entry parsed. Note that an empty description is managed and it will not
    # raise a parsing failure.
    lexer.Token('STRING', r'[ \t]*\r?\n', 'ParseMessage', 'INITIAL'),
    # The entry is not formatted as expected, so the parsing failed.
    lexer.Token('.', '([^\r\n]+)\r?\n', 'ParseFailed', 'INITIAL')
  ]

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    # Set local_zone to false, since timestamps are UTC.
    super(SELinuxParser, self).__init__(pre_obj, config, False)
    self.attributes = {'audit_type': '', 'pid': '', 'body': ''}
    self.timestamp = 0

  def ParseType(self, match, **_):
    """Parse the audit event type."""
    self.attributes['audit_type'] = match.group(1)

  def ParseTime(self, match, **_):
    """Parse the log timestamp."""
    # TODO: do something with match.group(3) ?
    try:
      number_of_seconds = int(match.group(1), 10)
      timestamp = timelib.Timestamp.FromPosixTime(number_of_seconds)
      timestamp += int(match.group(2), 10) * 1000
      self.timestamp = timestamp
    except ValueError as exception:
      logging.error(
          u'Unable to retrieve timestamp with error: {0:s}'.format(exception))
      self.timestamp = 0
      raise lexer.ParseError(u'Not a valid timestamp.')

  def ParseString(self, match, **unused_kwargs):
    """Add a string to the body attribute.

    This method extends the one from TextParser slightly,
    searching for the 'pid=[0-9]+' value inside the message body.
    """
    try:
      self.attributes['body'] += match.group(1)
      # TODO: fix it using lexer or remove pid parsing.
      # Indeed this is something that lexer is able to manage, but 'pid' field
      # is non positional: so, by doing the following step, the FSM is kept
      # simpler. Left the 'to do' as a reminder of possible refactoring.
      pid_search = self.PID_RE.search(self.attributes['body'])
      if pid_search:
        self.attributes['pid'] = pid_search.group(1)
    except IndexError:
      self.attributes['body'] += match.group(0).strip('\n')

  def ParseFailed(self, **unused_kwargs):
    """Entry parsing failed callback."""
    raise lexer.ParseError(u'Unable to parse SELinux log line.')

  def ParseLine(self, zone):
    """Parse a single line from the SELinux audit file.

    This method extends the one from TextParser slightly, creating a
    SELinux event with the timestamp (UTC) taken from log entries.

    Args:
      zone: The timezone of the host computer, not used since the
      timestamp are UTC.

    Returns:
      An event object (instance of EventObject) that is constructed
      from the selinux entry.
    """
    if not self.timestamp:
      raise errors.TimestampNotCorrectlyFormed(
          u'Unable to parse entry, timestamp not defined.')
    offset = getattr(self, 'entry_offset', 0)
    event_object = SELinuxLineEvent(self.timestamp, offset, self.attributes)
    self.timestamp = 0
    return event_object
