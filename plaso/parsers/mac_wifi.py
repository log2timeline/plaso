# -*- coding: utf-8 -*-
"""This file contains the wifi.log (Mac OS X) parser."""

import logging
import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class MacWifiLogEventData(events.EventData):
  """Mac Wifi log event data.

  Attributes:
    action (str): known WiFI action, for example connected to an AP,
        configured, etc. If the action is not known, the value is
        the message of the log (text variable).
    agent (str): name and identifier of process that generated the log message.
    function (str): name of function that generated the log message.
    text (str): log message
  """

  DATA_TYPE = u'mac:wifilog:line'

  def __init__(self):
    """Initializes event data."""
    super(MacWifiLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.agent = None
    self.function = None
    self.text = None


class MacWifiLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse text based on wifi.log file."""

  NAME = u'macwifi'
  DESCRIPTION = u'Parser for Mac OS X wifi.log files.'

  _ENCODING = u'utf-8'

  THREE_DIGITS = text_parser.PyparsingConstants.THREE_DIGITS
  THREE_LETTERS = text_parser.PyparsingConstants.THREE_LETTERS

  # Regular expressions for known actions.
  _CONNECTED_RE = re.compile(r'Already\sassociated\sto\s(.*)\.\sBailing')
  _WIFI_PARAMETERS_RE = re.compile(
      r'\[ssid=(.*?), bssid=(.*?), security=(.*?), rssi=')

  _KNOWN_FUNCTIONS = [
      u'airportdProcessDLILEvent',
      u'_doAutoJoin',
      u'_processSystemPSKAssoc']

  _AGENT = (
      pyparsing.Literal(u'<') +
      pyparsing.Combine(
          pyparsing.Literal(u'airportd') + pyparsing.CharsNotIn(u'>'),
          joinString='', adjacent=True).setResultsName(u'agent') +
      pyparsing.Literal(u'>'))

  _DATE_TIME = pyparsing.Group(
      THREE_LETTERS.setResultsName(u'day_of_week') +
      THREE_LETTERS.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS + pyparsing.Suppress('.') +
      THREE_DIGITS.setResultsName(u'milliseconds'))

  # Define how a log line should look like.
  _MAC_WIFI_KNOWN_FUNCTION_LINE = (
      _DATE_TIME.setResultsName(u'date_time') + _AGENT +
      pyparsing.oneOf(_KNOWN_FUNCTIONS).setResultsName(u'function') +
      pyparsing.Literal(u':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  _MAC_WIFI_LINE = (
      _DATE_TIME.setResultsName(u'date_time') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  _MAC_WIFI_HEADER = (
      _DATE_TIME.setResultsName(u'date_time') +
      pyparsing.Literal(u'***Starting Up***').setResultsName(u'text'))

  _DATE_TIME_TURNED_OVER_HEADER = pyparsing.Group(
      text_parser.PyparsingConstants.MONTH.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  _MAC_WIFI_TURNED_OVER_HEADER = (
      _DATE_TIME_TURNED_OVER_HEADER.setResultsName(u'date_time') +
      pyparsing.Combine(
          pyparsing.Word(pyparsing.printables) +
          pyparsing.Word(pyparsing.printables) +
          pyparsing.Literal(u'logfile turned over') +
          pyparsing.LineEnd(),
          joinString=u' ', adjacent=False).setResultsName(u'text'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'header', _MAC_WIFI_HEADER),
      (u'turned_over_header', _MAC_WIFI_TURNED_OVER_HEADER),
      (u'known_function_logline', _MAC_WIFI_KNOWN_FUNCTION_LINE),
      (u'logline', _MAC_WIFI_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser object."""
    super(MacWifiLogParser, self).__init__()
    self._last_month = 0
    self._year_use = 0

  def _GetAction(self, function, text):
    """Parse the well known actions for easy reading.

    Args:
      function (str): The function or action called by the agent.
      text (str): Mac Wifi log text.

    Returns:
       str: a formatted string representing the known (or common) action.
           If the action is not known the original log text is returned.
    """
    # TODO: replace "x in y" checks by startswith if possible.
    if u'airportdProcessDLILEvent' in function:
      interface = text.split()[0]
      return u'Interface {0:s} turn up.'.format(interface)

    if u'doAutoJoin' in function:
      match = self._CONNECTED_RE.match(text)
      if match:
        ssid = match.group(1)[1:-1]
      else:
        ssid = u'Unknown'
      return u'Wifi connected to SSID {0:s}'.format(ssid)

    if u'processSystemPSKAssoc' in function:
      wifi_parameters = self._WIFI_PARAMETERS_RE.search(text)
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

  def _GetTimeElementsTuple(self, key, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: contains:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
        milliseconds (int): milliseconds.
    """
    if key == u'turned_over_header':
      month, day, hours, minutes, seconds = structure.date_time

      milliseconds = 0
    else:
      _, month, day, hours, minutes, seconds, milliseconds = structure.date_time

    # Note that dfdatetime_time_elements.TimeElements will raise ValueError
    # for an invalid month.
    month = timelib.MONTH_DICT.get(month.lower(), 0)

    if month != 0 and month < self._last_month:
      # Gap detected between years.
      self._year_use += 1

    return (self._year_use, month, day, hours, minutes, seconds, milliseconds)

  def _ParseLogLine(self, parser_mediator, key, structure):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetTimeElementsTuple(key, structure)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid date time value: {0!s}'.format(structure.date_time))
      return

    self._last_month = time_elements_tuple[1]

    event_data = MacWifiLogEventData()
    event_data.agent = structure.agent
    # Due to the use of CharsNotIn pyparsing structure contains whitespaces
    # that need to be removed.
    event_data.function = structure.function.strip()
    event_data.text = structure.text

    if key == u'known_function_logline':
      event_data.action = self._GetAction(
          event_data.function, event_data.text)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseLogLine(parser_mediator, key, structure)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Mac Wifi log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (bytes): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    self._last_month = 0
    self._year_use = parser_mediator.GetEstimatedYear()

    key = u'header'

    try:
      structure = self._MAC_WIFI_HEADER.parseString(line)
    except pyparsing.ParseException:
      structure = None

    if not structure:
      key = u'turned_over_header'

      try:
        structure = self._MAC_WIFI_TURNED_OVER_HEADER.parseString(line)
      except pyparsing.ParseException:
        structure = None

    if not structure:
      logging.debug(u'Not a Mac Wifi log file')
      return False

    time_elements_tuple = self._GetTimeElementsTuple(key, structure)

    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logging.debug(
          u'Not a Mac Wifi log file, invalid date and time: {0!s}'.format(
              structure.date_time))
      return False

    self._last_month = time_elements_tuple[1]

    return True


manager.ParsersManager.RegisterParser(MacWifiLogParser)
