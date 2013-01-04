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
"""This file contains a syslog parser in plaso."""
import datetime
import logging

from plaso.lib import lexer
from plaso.lib import parser

__pychecker__ = 'no-funcdoc'


class Syslog(parser.TextParser):
  """Parse syslog files using the TextParser."""

  NAME = 'Syslog'

  # Define the tokens that make up the structure of a syslog file.
  tokens = [
      lexer.Token('INITIAL',
                  '(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) ',
                  'SetMonth', 'DAY'),
      lexer.Token('DAY', r'\s?(\d{1,2})\s+', 'SetDay', 'TIME'),
      lexer.Token('TIME', r'([0-9:\.]+) ', 'SetTime', 'STRING_HOST'),
      lexer.Token('STRING_HOST', r'^--(-)', 'ParseHost', 'STRING'),
      lexer.Token('STRING_HOST', r'([^\s]+) ', 'ParseHost', 'STRING_PID'),
      lexer.Token('STRING_PID', r'([^\:\n]+)', 'ParsePid', 'STRING'),
      lexer.Token('STRING', r'([^\n]+)', 'ParseString', ''),
      lexer.Token('STRING', r'\n\t', None, ''),
      lexer.Token('STRING', r'\t', None, ''),
      lexer.Token('STRING', r'\n', 'ParseMessage', 'INITIAL'),
      lexer.Token('.', '([^\n]+)\n', 'ParseIncomplete', 'INITIAL'),
      lexer.Token('.', '\n[^\t]', 'ParseIncomplete', 'INITIAL'),
      lexer.Token('S[.]+', '(.+)', 'ParseString', ''),
      ]

  def __init__(self, pre_obj):
    super(Syslog, self).__init__(pre_obj, True)
    # Set the initial year to 0 (fixed in the actual Parse method)
    # TODO this is a HACK to get the tests working let's discuss this
    self._year_use = getattr(pre_obj, 'year', 0)
    self._last_month = 0
    self.source_long = 'Syslog Log File'

    # Set some additional attributes.
    self.attributes['reporter'] = ''
    self.attributes['pid'] = ''

  def GetYear(self, stat, zone):
    time = stat.attributes.get('crtime', 0)
    if not time:
      time = stat.attributes.get('ctime', 0)

    if not time:
      logging.error(
          ('Unable to determine correct year of syslog file, using current '
           'year'))
      return datetime.datetime.now().year

    try:
      timestamp = datetime.datetime.fromtimestamp(time, zone)
    except ValueError as e:
      logging.error(
          ('Unable to determine correct year of syslog file, using current '
           'one, error msg: %s', e))
      return datetime.datetime.now().year

    return timestamp.year

  def ParseLine(self, zone):
    """Parse a single line from the syslog file.

    This method extends the one from TextParser slightly, adding
    the context of the reporter and pid values found inside syslog
    files.

    Args:
      zone: The timezone of the host computer.

    Returns:
      An EventObject that is constructed from the syslog entry.
    """
    if not self._year_use:
      # TODO Find a decent way to actually calculate the correct year
      # from the syslog file, instead of relying on stats object.
      stat = self.fd.Stat()
      self._year_use = self.GetYear(stat, zone)

      if not self._year_use:
        # TODO: Make this sensible, not have the year permanent.
        self._year_use = 2012

    if self._last_month > int(self.attributes['imonth']):
      self._year_use += 1

    self._last_month = int(self.attributes['imonth'])

    self.attributes['iyear'] = self._year_use

    if self.attributes['pid']:
      line = '[%s, pid: %d] %s' % (self.attributes['reporter'],
                                   self.attributes['pid'],
                                   self.attributes['body'])
    elif self.attributes['reporter']:
      line = '[%s] %s' % (self.attributes['reporter'], self.attributes['body'])
    else:
      line = self.attributes['body']

    self.attributes['body'] = line
    return super(Syslog, self).ParseLine(zone)

  def ParseHost(self, match, **_):
    self.attributes['hostname'] = match.group(1)

  def ParsePid(self, match, **_):
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

  def ParseString(self, match, **_):
    self.attributes['body'] += match.group(1)

  def PrintLine(self):
    self.attributes['iyear'] = 2012
    return super(Syslog, self).PrintLine()


