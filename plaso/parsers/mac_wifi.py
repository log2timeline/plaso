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
      timestamp (int): The timestamp, contains the number of microseconds from
          January 1, 1970 00:00:00 UTC.
      agent (str): The process responsible for this log message.
      function (str): The function being called by the process.
      text (str): The log message
      action (str): A string containing known WiFI actions, e.g. connected to
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

  _KNOWN_FUNCTIONS = [
      u'airportdProcessDLILEvent',
      u'_doAutoJoin',
      u'_processSystemPSKAssoc']

  # Define how a log line should look like.
  WIFI_KNOWN_FUNCTION_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.Literal(u'<') +
      pyparsing.Combine(pyparsing.Literal(u'airportd') +
                        pyparsing.CharsNotIn(u'>'),
                        joinString='',
                        adjacent=True).setResultsName(u'agent') +
      pyparsing.Literal(u'>') +
      pyparsing.oneOf(_KNOWN_FUNCTIONS).setResultsName(u'function') +
      pyparsing.Literal(u':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  WIFI_LINE = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  WIFI_HEADER = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'day_of_week') +
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_MSEC.setResultsName(u'time') +
      pyparsing.Literal(u'***Starting Up***').setResultsName(u'text'))

  WIFI_TURNED_OVER_HEADER = (
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time') +
      pyparsing.Combine(pyparsing.Word(pyparsing.printables) +
                        pyparsing.Word(pyparsing.printables) +
                        pyparsing.Literal(u'logfile turned over') +
                        pyparsing.LineEnd(), joinString=u' ', adjacent=False
                       ).setResultsName(u'text'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'header', WIFI_HEADER),
      (u'turned_over_header', WIFI_TURNED_OVER_HEADER),
      (u'known_function_logline', WIFI_KNOWN_FUNCTION_LINE),
      (u'logline', WIFI_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser object."""
    super(MacWifiLogParser, self).__init__()
    self._last_month = None
    self._year_use = 0

  def _GetAction(self, function, text):
    """Parse the well known actions for easy reading.

    Args:
      function (str): The function or action called by the agent.
      text (str): Mac Wifi log text.

    Returns:
       str: A formatted string representing the known (or common) action.
           If the action is not known the original log text is returned.
    """

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
      day (int): an integer representing the day.
      month (int) : an integer representing the month.
      year (int): an integer representing the year.
      time (list[int]): a list containing integers with the number of
          hours, minutes and seconds.

    Returns:
      int: The timestamp which is an integer containing the number of
          micro seconds since January 1, 1970, 00:00:00 UTC.

    Raises:
      TimestampError: if the timestamp cannot be created from the date and
                      time values.
    """
    try:
      time_values, milliseconds = time
      hours, minutes, seconds = time_values
      microseconds = milliseconds * 1000
      return timelib.Timestamp.FromTimeParts(
          year, month, day, hours, minutes, seconds, microseconds=microseconds)
    except ValueError:
      hours, minutes, seconds = time
      return timelib.Timestamp.FromTimeParts(
          year, month, day, hours, minutes, seconds)

  def _ParseLogLine(self, parser_mediator, structure, key):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): A parser mediator object.
      structure (pyparsing.ParseResults): A pyparsing.ParseResults object
          from a line in the log file.
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
      parser_mediator.ProduceExtractionError(
          u'Unable to determine timestamp with error: {0:s}'.format(
              exception))
      return

    self._last_month = month

    text = structure.text
    function = structure.function.strip()

    if key != 'known_function_logline':
      action = ''
    else:
      action = self._GetAction(function, text)

    event_object = MacWifiLogEvent(
        timestamp, structure.agent, function, text, action)

    parser_mediator.ProduceEvent(event_object)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (pyparsing.ParseResults): A parser mediator object.
      key (str): An identification string indicating the name of the parsed
          structure.
      structure (pyparsing.ParseResults): A pyparsing.ParseResults object
          from a line in the log file.
    """

    if key not in self._SUPPORTED_KEYS:
      logging.debug(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))
      return

    self._ParseLogLine(parser_mediator, structure, key)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Mac Wifi log file.

    Args:
      parser_mediator (ParserMediator): A parser mediator object.
      line (str): A single line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      _ = self.WIFI_HEADER.parseString(line)
    except pyparsing.ParseException:
      try:
        _ = self.WIFI_TURNED_OVER_HEADER.parseString(line)
      except pyparsing.ParseException:
        logging.debug(u'Not a Mac Wifi log file')
        return False
    return True


manager.ParsersManager.RegisterParser(MacWifiLogParser)
