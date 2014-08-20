#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a syslog parser in plaso."""

import datetime
import logging

from plaso.lib import event
from plaso.lib import lexer
from plaso.lib import timelib
from plaso.lib import utils
from plaso.parsers import text_parser


class SyslogLineEvent(event.TextEvent):
  """Convenience class for a syslog line event."""
  DATA_TYPE = 'syslog:line'

  def __init__(self, timestamp, offset, attributes):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the event.
      attributes: A dict that contains the events attributes
    """
    super(SyslogLineEvent, self).__init__(timestamp, attributes)
    self.offset = offset


class SyslogParser(text_parser.SlowLexicalTextParser):
  """Parse text based syslog files."""

  NAME = 'syslog'

  # TODO: can we change this similar to SQLite where create an
  # event specific object for different lines using a callback function.
  # Define the tokens that make up the structure of a syslog file.
  tokens = [
      lexer.Token('INITIAL',
                  '(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) ',
                  'SetMonth', 'DAY'),
      lexer.Token('DAY', r'\s?(\d{1,2})\s+', 'SetDay', 'TIME'),
      lexer.Token('TIME', r'([0-9:\.]+) ', 'SetTime', 'STRING_HOST'),
      lexer.Token('STRING_HOST', r'^--(-)', 'ParseHostname', 'STRING'),
      lexer.Token('STRING_HOST', r'([^\s]+) ', 'ParseHostname', 'STRING_PID'),
      lexer.Token('STRING_PID', r'([^\:\n]+)', 'ParsePid', 'STRING'),
      lexer.Token('STRING', r'([^\n]+)', 'ParseString', ''),
      lexer.Token('STRING', r'\n\t', None, ''),
      lexer.Token('STRING', r'\t', None, ''),
      lexer.Token('STRING', r'\n', 'ParseMessage', 'INITIAL'),
      lexer.Token('.', '([^\n]+)\n', 'ParseIncomplete', 'INITIAL'),
      lexer.Token('.', '\n[^\t]', 'ParseIncomplete', 'INITIAL'),
      lexer.Token('S[.]+', '(.+)', 'ParseString', ''),
      ]

  def __init__(self):
    """Initializes a syslog parser object."""
    super(SyslogParser, self).__init__(local_zone=True)
    # Set the initial year to 0 (fixed in the actual Parse method)
    self._year_use = 0
    self._last_month = 0

    # Set some additional attributes.
    self.attributes['reporter'] = ''
    self.attributes['pid'] = ''

  def _GetYear(self, stat, timezone):
    """Retrieves the year either from the input file or from the settings."""
    time = getattr(stat, 'crtime', 0)
    if not time:
      time = getattr(stat, 'ctime', 0)

    if not time:
      current_year = timelib.GetCurrentYear()
      logging.error((
          u'Unable to determine year of syslog file.\nDefautling to: '
          u'{0:d}').format(current_year))
      return current_year

    try:
      timestamp = datetime.datetime.fromtimestamp(time, timezone)
    except ValueError as exception:
      current_year = timelib.GetCurrentYear()
      logging.error(
          u'Unable to determine year of syslog file with error: {0:s}\n'
          u'Defaulting to: {1:d}'.format(exception, current_year))
      return current_year

    return timestamp.year

  def ParseLine(self, parser_context):
    """Parse a single line from the syslog file.

    This method extends the one from TextParser slightly, adding
    the context of the reporter and pid values found inside syslog
    files.

    Args:
      parser_context: A parser context object (instance of ParserContext).

    Returns:
      An event object (instance of TextEvent).
    """
    # Note this an older comment applying to a similar approach previously
    # the init function.
    # TODO: this is a HACK to get the tests working let's discuss this.
    if not self._year_use:
      self._year_use = parser_context.year

    if not self._year_use:
      # TODO: Find a decent way to actually calculate the correct year
      # from the syslog file, instead of relying on stats object.
      stat = self.file_entry.GetStat()
      self._year_use = self._GetYear(stat, parser_context.timezone)

      if not self._year_use:
        # TODO: Make this sensible, not have the year permanent.
        self._year_use = 2012

    month_compare = int(self.attributes['imonth'])
    if month_compare and self._last_month > month_compare:
      self._year_use += 1

    self._last_month = int(self.attributes['imonth'])

    self.attributes['iyear'] = self._year_use

    return super(SyslogParser, self).ParseLine(parser_context)

  def ParseHostname(self, match=None, **unused_kwargs):
    """Parses the hostname.

       This is a callback function for the text parser (lexer) and is
       called by the STRING_HOST lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes['hostname'] = match.group(1)

  def ParsePid(self, match=None, **unused_kwargs):
    """Parses the process identifier (PID).

       This is a callback function for the text parser (lexer) and is
       called by the STRING_PID lexer state.

    Args:
      match: The regular expression match object.
    """
    # TODO: Change this logic and rather add more Tokens that
    # fully cover all variations of the various PID stages.
    line = match.group(1)
    if line[-1] == ']':
      splits = line.split('[')
      if len(splits) == 2:
        self.attributes['reporter'], pid = splits
      else:
        pid = splits[-1]
        self.attributes['reporter'] = '['.join(splits[:-1])
      try:
        self.attributes['pid'] = int(pid[:-1])
      except ValueError:
        self.attributes['pid'] = 0
    else:
      self.attributes['reporter'] = line

  def ParseString(self, match=None, **unused_kwargs):
    """Parses a (body text) string.

       This is a callback function for the text parser (lexer) and is
       called by the STRING lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes['body'] += utils.GetUnicodeString(match.group(1))

  def PrintLine(self):
    """Prints a log line."""
    self.attributes['iyear'] = 2012
    return super(SyslogParser, self).PrintLine()

  # TODO: this is a rough initial implementation to get this working.
  def CreateEvent(self, timestamp, offset, attributes):
    """Creates a syslog line event.

       This overrides the default function in TextParser to create
       syslog line events instead of text events.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the event.
      attributes: A dict that contains the events attributes.

    Returns:
      A text event (SyslogLineEvent).
    """
    return SyslogLineEvent(timestamp, offset, attributes)

