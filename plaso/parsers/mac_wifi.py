# -*- coding: utf-8 -*-
"""This file contains the wifi.log (Mac OS X) parser."""

import logging
import re

import pyparsing

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class MacWifiLogEvent(time_events.TimestampEvent):
  """Convenience class for a Mac Wifi log line event."""

  DATA_TYPE = u'mac:wifilog:line'

  def __init__(self, timestamp, agent, function, text, action):
    """Initializes the event object.

    Args:
      timestamp: the timestamp, contains the number of microseconds from
                 January 1, 1970 00:00:00 UTC.
      agent: TODO
      function: TODO
      text: The log message
      action: A string containing known WiFI actions, eg: connected to
              an AP, configured, etc. If the action is not known,
              the value is the message of the log (text variable).
    """
    super(MacWifiLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.agent = agent
    self.function = function
    self.text = text
    self.action = action


class MacWifiLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse text based on wifi.log file."""

  NAME = u'macwifi'
  DESCRIPTION = u'Parser for Mac OS X wifi.log files.'

  _ENCODING = u'utf-8'

  # Regular expressions for known actions.
  RE_CONNECTED = re.compile(r'Already\sassociated\sto\s(.*)\.\sBailing')
  RE_WIFI_PARAMETERS = re.compile(
      r'\[ssid=(.*?), bssid=(.*?), security=(.*?), rssi=')

  # Define how a log line should look like.
  WIFI_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.Literal(u'<') +
      pyparsing.CharsNotIn(u'>').setResultsName(u'agent') +
      pyparsing.Literal(u'>') +
      pyparsing.CharsNotIn(u':').setResultsName(u'function') +
      pyparsing.Literal(u':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  WIFI_HEADER = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.Literal(u'***Starting Up***'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', WIFI_LINE),
      (u'header', WIFI_HEADER)]

  def __init__(self):
    """Initializes a parser object."""
    super(MacWifiLogParser, self).__init__()
    self._year_use = 0
    self._last_month = None

  def _GetAction(self, agent, function, text):
    """Parse the well know actions for easy reading.

    Args:
      agent: The device that generate the entry.
      function: The function or action called by the agent.
      text: Mac Wifi log text.

    Returns:
      know_action: A formatted string representing the known (or common) action.
    """
    if not agent.startswith(u'airportd'):
      return text

    # TODO: replace "x in y" checks by startswith if possible.
    if u'airportdProcessDLILEvent' in function:
      interface = text.split()[0]
      return u'Interface {0:s} turn up.'.format(interface)

    if u'doAutoJoin' in function:
      match = re.match(self.RE_CONNECTED, text)
      if match:
        ssid = match.group(1)[1:-1]
      else:
        ssid = u'Unknown'
      return u'Wifi connected to SSID {0:s}'.format(ssid)

    if u'processSystemPSKAssoc' in function:
      wifi_parameters = self.RE_WIFI_PARAMETERS.search(text)
      if wifi_parameters:
        ssid = wifi_parameters.group(1)
        bssid = wifi_parameters.group(2)
        security = wifi_parameters.group(3)
        if not ssid:
          ssid = u'Unknown'
        if not bssid:
          bssid = u'Unknown'
        if not security:
          security = u'Unknown'
        return (
            u'New wifi configured. BSSID: {0:s}, SSID: {1:s}, '
            u'Security: {2:s}.').format(bssid, ssid, security)
    return text

  def _ConvertToTimestamp(self, day, month, year, time):
    """Converts date and time values into a timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    08, Nov, [20, 36, 37], 222]

    Args:
      day: an integer representing the day.
      month: an integer representing the month.
      year: an integer representing the year.
      time: a list containing integers with the number of
            hours, minutes and seconds.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.

    Raises:
      TimestampError: if the timestamp cannot be created from the date and
                      time values.
    """
    time_values, milliseconds = time
    hours, minutes, seconds = time_values
    microseconds = milliseconds * 1000
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hours, minutes, seconds, microseconds=microseconds)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if not self._year_use:
      self._year_use = parser_mediator.GetEstimatedYear()

    # Gap detected between years.
    month = timelib.MONTH_DICT.get(structure.month.lower())
    if not self._last_month:
      self._last_month = month

    if month < self._last_month:
      self._year_use += 1

    try:
      timestamp = self._ConvertToTimestamp(
          structure.day, month, self._year_use, structure.time)
    except errors.TimestampError as exception:
      parser_mediator.ProduceParseError(
          u'unable to determine timestamp with error: {0:s}'.format(
              exception))
      return

    self._last_month = month

    text = structure.text

    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    function = structure.function.strip()
    action = self._GetAction(structure.agent, function, text)
    event_object = MacWifiLogEvent(
        timestamp, structure.agent, function, text, action)
    parser_mediator.ProduceEvent(event_object)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key == u'logline':
      self._ParseLogLine(parser_mediator, structure)
    elif key != u'header':
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Mac Wifi log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      _ = self.WIFI_HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a Mac Wifi log file')
      return False
    return True


manager.ParsersManager.RegisterParser(MacWifiLogParser)
