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
"""This file contains a appfirewall.log (Mac OS X Firewall) parser."""

import datetime
import logging

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import text_parser
from plaso.lib import timelib

import pyparsing
import pytz


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class MacAppFirewallLogEvent(event.TimestampEvent):
  """Convenience class for a Mac Wifi log line event."""

  DATA_TYPE = 'mac:asl:appfirewall:line'

  def __init__(self, timestamp, structure, process_name, action):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value, epoch.
      structure: structure with the parse fields.
          computer_name: string with the name of the computer.
          agent: string with the agent that save the log.
          status: string with the saved status action.
          process_name: string name of the entity that tried do the action.
      action: string with the action
    """
    super(MacAppFirewallLogEvent, self).__init__(timestamp,
        eventdata.EventTimestamp.ADDED_TIME)
    self.timestamp = timestamp
    self.computer_name = structure.computer_name
    self.agent = structure.agent
    self.status = structure.status
    self.process_name = process_name
    self.action = action


class MacAppFirewallParser(text_parser.PyparsingSingleLineTextParser):
  """Parse text based on appfirewall.log file."""
  NAME = 'mac_appfirewall_log'

  # Regular expressions for known actions.

  # Define how a log line should look like.
  # Example: 'Nov  2 04:07:35 DarkTemplar-2.local socketfilterfw[112] '
  #          '<Info>: Dropbox: Allow (in:0 out:2)'
  # INFO: process_name is going to have a white space at the beginning.
  FIREWALL_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME.setResultsName('time') +
      pyparsing.Word(pyparsing.printables).setResultsName('computer_name') +
      pyparsing.Word(pyparsing.printables).setResultsName('agent') +
      pyparsing.Literal(u'<').suppress() +
      pyparsing.CharsNotIn(u'>').setResultsName('status') +
      pyparsing.Literal(u'>:').suppress() +
      pyparsing.CharsNotIn(u':').setResultsName('process_name') +
      pyparsing.Literal(u':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('action'))

  # Repeated line.
  # Example: Nov 29 22:18:29 --- last message repeated 1 time ---
  REPEATED_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME.setResultsName('time') +
      pyparsing.Literal(u'---').suppress() +
      pyparsing.CharsNotIn(u'---').setResultsName('process_name') +
      pyparsing.Literal(u'---').suppress())

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', FIREWALL_LINE),
      ('repeated', REPEATED_LINE)]

  def __init__(self, pre_obj, config):
    """Initialize the parser."""
    super(MacAppFirewallParser, self).__init__(pre_obj, config)
    self._year_use = getattr(pre_obj, 'year', 0)
    self.local_zone = getattr(pre_obj, 'zone', pytz.utc)
    self._last_month = None
    self.previous_structure = None

  def VerifyStructure(self, line):
    """Verify that this file is a Mac AppFirewall log file."""
    try:
      line = self.FIREWALL_LINE.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a Mac AppFirewall log file')
      return False
    if (line.action != 'creating /var/log/appfirewall.log' or
        line.status != 'Error'):
      return False
    return True

  def ParseRecord(self, key, structure):
    """Parse each record structure and return an EventObject if applicable."""
    if key == 'logline' or key == 'repeated':
      return self._ParseLogLine(structure, key)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def _ParseLogLine(self, structure, key):
    """Parse a logline and store appropriate attributes.

    Args:
      structure: log line of structure.
      key: type of line log (normal or repeated).

    Returns:
      Return an object MacAppFirewallLogEvent.
    """
    # TODO: improving this to get a valid year.
    if not self._year_use:
      # Get from the creation time of the file.
      self._year_use = self._GetYear(self.file_entry.GetStat(), self.local_zone)
      # If fail, get from the current time.
      if not self._year_use:
        self._year_use = timelib.GetCurrentYear()

    # Gap detected between years.
    month = timelib.MONTH_DICT.get(structure.month.lower())
    if not self._last_month:
      self._last_month = month
    if month < self._last_month:
      self._year_use += 1
    timestamp = self._GetTimestamp(
        structure.day,
        month,
        self._year_use,
        structure.time)
    if not timestamp:
      logging.debug(u'Invalid timestamp {}'.format(structure.timestamp))
      return
    self._last_month = month

    # If the actual entry is a repeated entry, we take the basic information
    # from the previous entry, but using the timestmap from the actual entry.
    if key == 'logline':
      self.previous_structure = structure
    else:
      structure = self.previous_structure

    # Pyparsing reads in RAW, but the text is in UTF8.
    try:
      action = structure.action.decode('utf-8')
    except UnicodeDecodeError:
      logging.warning(
          u'Decode UTF8 failed, the message string may be cut short.')
      action = structure.action.decode('utf-8', 'ignore')
    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    process_name = structure.process_name.strip()

    event_object = MacAppFirewallLogEvent(
        timestamp, structure, process_name, action)
    return event_object

  def _GetTimestamp(self, day, month, year, time):
    """Gets a timestamp from a pyparsing ParseResults timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    08, Nov, [20, 36, 37]

    Args:
      timestamp_string: The pyparsing ParseResults object

    Returns:
      day: An integer representing the day.
      month: An integer representing the month.
      year: An integer representing the year.
      timestamp: A plaso timelib timestamp event or 0.
    """
    try:
      hour, minute, second = time
      timestamp = timelib.Timestamp.FromTimeParts(
          year, month, int(day, 10), hour, minute, second)
    except ValueError:
      timestamp = 0
    return timestamp

  def _GetYear(self, stat, zone):
    """Retrieves the year either from the input file or from the settings."""
    time = stat.attributes.get('crtime', 0)
    if not time:
      time = stat.attributes.get('ctime', 0)

    if not time:
      logging.error(
          u'Unable to determine correct year of log file, defaulting to '
          u'current year.')
      return timelib.GetCurrentYear()

    try:
      timestamp = datetime.datetime.fromtimestamp(time, zone)
    except ValueError as exception:
      logging.error((
          u'Unable to determine correct year of log file with error: {0:s}, '
          u'defaulting to current year.').format(exception))
      return timelib.GetCurrentYear()
    return timestamp.year

