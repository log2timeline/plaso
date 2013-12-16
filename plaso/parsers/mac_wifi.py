#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains the wifi.log (Mac OS X) parser."""

import datetime
import logging
import re
import pyparsing
import pytz

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import text_parser
from plaso.lib import timelib

__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class MacWifiLogEvent(event.TimestampEvent):
  """Convenience class for a Mac Wifi log line event."""

  DATA_TYPE = 'mac:wifilog:line'

  def __init__(self, timestamp, agent, function, text, action):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value, epoch.
      source_code: Details of the source code file generating the event.
      log_level: The log level used for the event.
      text: The log message
      action: A string containing known WiFI actions, eg: connected to
              an AP, configured, etc. If the action is not known,
              the value is the message of the log (text variable).
    """
    super(MacWifiLogEvent, self).__init__(timestamp,
        eventdata.EventTimestamp.ADDED_TIME)
    self.agent = agent
    self.function = function
    self.text = text
    self.action = action


class MacWifiLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse text based on wifi.log file."""

  NAME = 'macwifi'

  # Regular expressions for known actions.
  RE_CONNECTED = r'Already\sassociated\sto\s(.*)\.\sBailing'
  RE_ASSOCIATE_SSID = r'(?<=\[ssid=).*?(?=, bssid=)'
  RE_ASSOCIATE_BSSID = r'(?<=bssid=).*?(?=, security=)'
  RE_ASSOCIATE_SECURITY = r'(?<=security=).*?(?=, rssi=)'

  # Define how a log line should look like.
  WIFI_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName('day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName('time') +
      pyparsing.Literal(u'<') +
      pyparsing.CharsNotIn(u'>').setResultsName('agent') +
      pyparsing.Literal(u'>') +
      pyparsing.CharsNotIn(u':').setResultsName('function') +
      pyparsing.Literal(u':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  WIFI_HEADER = (
      text_parser.PyparsingConstants.MONTH.setResultsName('day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName('time') +
      pyparsing.Literal(u'***Starting Up***'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', WIFI_LINE),
      ('header', WIFI_HEADER)]

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(MacWifiLogParser, self).__init__(pre_obj, config)
    self._year_use = getattr(pre_obj, 'year', 0)
    self.local_zone = getattr(pre_obj, 'zone', pytz.utc)
    self._last_month = None

  def VerifyStructure(self, line):
    """Verify that this file is a Mac Wifi log file."""
    try:
      _ = self.WIFI_HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a Mac Wifi log file')
      return False
    return True

  def ParseRecord(self, key, structure):
    """Parse each record structure and return an EventObject if applicable."""
    if key == 'logline':
      return self._ParseLogLine(structure)
    elif key != 'header':
      logging.warning(u'Unable to parse record, unknown structure: %s' % key)

  def _ParseLogLine(self, structure):
    """Parse a logline and store appropriate attributes."""
    # TODO: improving this to get a valid year.
    if not self._year_use:
      # Get from the creation time of the file.
      self._year_use = self._GetYear(self.fd.Stat(), self.local_zone)
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
    self.last_month = month

    # Pyparsing reads in RAW, but the text is in UTF8.
    try:
      text = structure.text.decode('utf-8')
    except UnicodeDecodeError:
      logging.warning(
          'Decode UTF8 failed, the message string may be cut short.')
      text = structure.text.decode('utf-8', 'ignore')

    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    function = structure.function.strip()
    event_object = MacWifiLogEvent(
        timestamp, structure.agent, function, text,
        self._GetAction(structure.agent, function, text))
    return event_object

  def _GetTimestamp(self, day, month, year, time):
    """Gets a timestamp from a pyparsing ParseResults timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    08, Nov, [20, 36, 37], 222]

    Args:
      timestamp_string: The pyparsing ParseResults object

    Returns:
      day: An integer representing the day.
      month: An integer representing the month.
      year: An integer representing the year.
      timestamp: A plaso timelib timestamp event or 0.
    """
    try:
      time_part, millisecond = time
      microsec = millisecond * 1000
      hour, minute, second = time_part
      timestamp = timelib.Timestamp.FromTimeParts(
          year, month, int(day, 10), hour, minute, second, microsec)
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
          ('Unable to determine correct year of syslog file, using current '
           'year'))
      return timelib.GetCurrentYear()

    try:
      timestamp = datetime.datetime.fromtimestamp(time, zone)
    except ValueError as e:
      logging.error(
          ('Unable to determine correct year of syslog file, using current '
           'one, error msg: %s', e))
      return timelib.GetCurrentYear()
    return timestamp.year

  def _GetAction(self, agent, function, text):
    """Parse the well know actions for easy reading.

    Args:
      agent: The device that generate the entry.
      function: The function or action called by the agent.
      text: Mac Wifi log text.

    Returns:
      know_action: A formatted string representing the known (or common) action.
    """
    if not agent.startswith('airportd'):
      return text

    if 'airportdProcessDLILEvent' in function:
      interface = text.split()[0]
      return u'Interface {} turn up.'.format(interface)

    if 'doAutoJoin' in function:
      match = re.match(self.RE_CONNECTED, text)
      if match:
        ssid = match.group(1)[1:-1]
      else:
        ssid = 'Unknown'
      return u'Wifi connected to SSID {}'.format(ssid)

    if 'processSystemPSKAssoc' in function:
      ssid = re.match(self.RE_ASSOCIATE_SSID, text)
      if not ssid:
        ssid = 'Unknown'
      bssid = re.match(self.RE_ASSOCIATE_BSSID, text)
      if not bssid:
        bssid = 'Unknown'
      security = re.match(self.RE_ASSOCIATE_SECURITY, text)
      if not security:
        security = 'Unknown'
      return u'New wifi configured. BSSID: {} SSID: {}, Security: {}.'.format(
          bssid, ssid, security)
    return text

