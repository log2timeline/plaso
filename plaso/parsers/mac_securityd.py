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
"""This file contains the ASL securityd log plaintext parser."""

import datetime
import logging

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import text_parser
from plaso.lib import timelib

import pyparsing
import pytz


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# INFO:
# http://opensource.apple.com/source/Security/Security-55471/sec/securityd/


class MacSecuritydLogEvent(time_events.TimestampEvent):
  """Convenience class for a ASL securityd line event."""

  DATA_TYPE = 'mac:asl:securityd:line'

  def __init__(
      self, timestamp, structure, sender, sender_pid,
      security_api, caller, message):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value, epoch.
      structure: Structure with the parse fields.
        level: String with the text representation of the priority level.
        facility: String with the ASL facility.
      sender: String with the name of the sender.
      sender_pid: Process id of the sender.
      security_api: Securityd function name.
      caller: The caller field, a string containing two hex numbers.
      message: String with the ASL message.
    """
    super(MacSecuritydLogEvent, self).__init__(
        timestamp,
        eventdata.EventTimestamp.ADDED_TIME)
    self.timestamp = timestamp
    self.level = structure.level
    self.sender_pid = sender_pid
    self.facility = structure.facility
    self.sender = sender
    self.security_api = security_api
    self.caller = caller
    self.message = message


class MacSecuritydLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the securityd file that contains logs from the security daemon."""

  NAME = 'mac_securityd'

  ENCODING = u'utf-8'

  # Default ASL Securityd log.
  SECURITYD_LINE = (
    text_parser.PyparsingConstants.MONTH.setResultsName('month') +
    text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
    text_parser.PyparsingConstants.TIME.setResultsName('time') +
    pyparsing.CharsNotIn(u'[').setResultsName('sender') +
    pyparsing.Literal(u'[').suppress() +
    text_parser.PyparsingConstants.PID.setResultsName('sender_pid') +
    pyparsing.Literal(u']').suppress() +
    pyparsing.Literal(u'<').suppress() +
    pyparsing.CharsNotIn(u'>').setResultsName('level') +
    pyparsing.Literal(u'>').suppress() +
    pyparsing.Literal(u'[').suppress() +
    pyparsing.CharsNotIn(u'{').setResultsName('facility') +
    pyparsing.Literal(u'{').suppress() +
    pyparsing.Optional(pyparsing.CharsNotIn(
        u'}').setResultsName('security_api')) +
    pyparsing.Literal(u'}').suppress() +
    pyparsing.Optional(pyparsing.CharsNotIn(u']:').setResultsName('caller')) +
    pyparsing.Literal(u']:').suppress() +
    pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('message'))

  # Repeated line.
  REPEATED_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME.setResultsName('time') +
      pyparsing.Literal(u'--- last message repeated').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('times') +
      pyparsing.Literal(u'time ---').suppress())

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', SECURITYD_LINE),
      ('repeated', REPEATED_LINE)]

  def __init__(self, pre_obj, config=None):
    """Initialize the parser."""
    super(MacSecuritydLogParser, self).__init__(pre_obj, config)
    self._year_use = getattr(pre_obj, 'year', 0)
    self.local_zone = getattr(pre_obj, 'zone', pytz.utc)
    self._last_month = None
    self.previous_structure = None

  def VerifyStructure(self, line):
    """Verify that this file is a ASL securityd log file."""
    try:
      line = self.SECURITYD_LINE.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a ASL securityd log file')
      return False
    # Check if the day, month and time is valid taking a random year.
    month = timelib.MONTH_DICT.get(line.month.lower())
    if not month:
      return False
    if self._GetTimestamp(line.day, month, 2012, line.time) == 0:
      return False
    return True

  def ParseRecord(self, key, structure):
    """Parse each record structure and return an EventObject if applicable."""
    if key == 'repeated' or key == 'logline':
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
      Return an object log event.
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

    if key == 'logline':
      self.previous_structure = structure
      message = structure.message
    else:
      times = structure.times
      structure = self.previous_structure
      message = u'Repeated {} times: {}'.format(
          times, structure.message)

    # It uses CarsNotIn structure which leaves whitespaces
    # at the beginning of the sender and the caller.
    sender = structure.sender.strip()
    caller = structure.caller.strip()
    if not caller:
      caller = 'unknown'
    if not structure.security_api:
      security_api = u'unknown'
    else:
      security_api = structure.security_api

    return MacSecuritydLogEvent(
        timestamp, structure, sender, structure.sender_pid, security_api,
        caller, message)

  def _GetTimestamp(self, day, month, year, time):
    """Gets a timestamp from a pyparsing ParseResults timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    08, Nov, [20, 36, 37]

    Args:
      day: An integer representing the day.
      month: An integer representing the month.
      year: An integer representing the year.
      time: A list containing the hours, minutes, seconds.

    Returns:
      timestamp: A plaso timestamp.
    """
    hours, minutes, seconds = time
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hours, minutes, seconds)

  def _GetYear(self, stat, zone):
    """Retrieves the year either from the input file or from the settings."""
    time = getattr(stat, 'crtime', 0)
    if not time:
      time = getattr(stat, 'ctime', 0)

    if not time:
      current_year = timelib.GetCurrentYear()
      logging.error((
          u'Unable to determine year of log file.\nDefaulting to: '
          u'{0:d}').format(current_year))
      return current_year

    try:
      timestamp = datetime.datetime.fromtimestamp(time, zone)
    except ValueError:
      current_year = timelib.GetCurrentYear()
      logging.error((
          u'Unable to determine year of log file.\nDefaulting to: '
          u'{0:d}').format(current_year))
      return current_year

    return timestamp.year
