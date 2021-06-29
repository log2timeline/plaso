# -*- coding: utf-8 -*-
"""Parses for MacOS Wifi log (wifi.log) files."""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


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

  DATA_TYPE = 'mac:wifilog:line'

  def __init__(self):
    """Initializes event data."""
    super(MacWifiLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.agent = None
    self.function = None
    self.text = None


class MacWifiLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses MacOS Wifi log (wifi.log) files."""

  NAME = 'macwifi'
  DATA_FORMAT = 'MacOS Wifi log (wifi.log) file'

  _ENCODING = 'utf-8'

  THREE_DIGITS = text_parser.PyparsingConstants.THREE_DIGITS
  THREE_LETTERS = text_parser.PyparsingConstants.THREE_LETTERS

  # Regular expressions for known actions.
  _CONNECTED_RE = re.compile(r'Already\sassociated\sto\s(.*)\.\sBailing')
  _WIFI_PARAMETERS_RE = re.compile(
      r'\[ssid=(.*?), bssid=(.*?), security=(.*?), rssi=')

  _KNOWN_FUNCTIONS = [
      'airportdProcessDLILEvent',
      '_doAutoJoin',
      '_processSystemPSKAssoc']

  _AGENT = (
      pyparsing.Literal('<') +
      pyparsing.Combine(
          pyparsing.Literal('airportd') + pyparsing.CharsNotIn('>'),
          joinString='', adjacent=True).setResultsName('agent') +
      pyparsing.Literal('>'))

  _DATE_TIME = pyparsing.Group(
      THREE_LETTERS.setResultsName('day_of_week') +
      THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS + pyparsing.Suppress('.') +
      THREE_DIGITS.setResultsName('milliseconds'))

  # Log line with a known function name.
  _MAC_WIFI_KNOWN_FUNCTION_LINE = (
      _DATE_TIME.setResultsName('date_time') + _AGENT +
      pyparsing.oneOf(_KNOWN_FUNCTIONS).setResultsName('function') +
      pyparsing.Literal(':') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  # Log line with an unknown function name.
  _MAC_WIFI_LINE = (
      _DATE_TIME.setResultsName('date_time') + pyparsing.NotAny(
          _AGENT +
          pyparsing.oneOf(_KNOWN_FUNCTIONS) +
          pyparsing.Literal(':')) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  _MAC_WIFI_HEADER = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('***Starting Up***').setResultsName('text'))

  _DATE_TIME_TURNED_OVER_HEADER = pyparsing.Group(
      text_parser.PyparsingConstants.MONTH.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  _MAC_WIFI_TURNED_OVER_HEADER = (
      _DATE_TIME_TURNED_OVER_HEADER.setResultsName('date_time') +
      pyparsing.Combine(
          pyparsing.Word(pyparsing.printables) +
          pyparsing.Word(pyparsing.printables) +
          pyparsing.Literal('logfile turned over') +
          pyparsing.LineEnd(),
          joinString=' ', adjacent=False).setResultsName('text'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('header', _MAC_WIFI_HEADER),
      ('turned_over_header', _MAC_WIFI_TURNED_OVER_HEADER),
      ('known_function_logline', _MAC_WIFI_KNOWN_FUNCTION_LINE),
      ('logline', _MAC_WIFI_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser."""
    super(MacWifiLogParser, self).__init__()
    self._last_month = 0
    self._year_use = 0

  def _GetAction(self, action, text):
    """Parse the well known actions for easy reading.

    Args:
      action (str): the function or action called by the agent.
      text (str): mac Wifi log text.

    Returns:
       str: a formatted string representing the known (or common) action.
           If the action is not known the original log text is returned.
    """
    # TODO: replace "x in y" checks by startswith if possible.
    if 'airportdProcessDLILEvent' in action:
      interface = text.split()[0]
      return 'Interface {0:s} turn up.'.format(interface)

    if 'doAutoJoin' in action:
      match = self._CONNECTED_RE.match(text)
      if match:
        ssid = match.group(1)[1:-1]
      else:
        ssid = 'Unknown'
      return 'Wifi connected to SSID {0:s}'.format(ssid)

    if 'processSystemPSKAssoc' in action:
      wifi_parameters = self._WIFI_PARAMETERS_RE.search(text)
      if wifi_parameters:
        ssid = wifi_parameters.group(1)
        bssid = wifi_parameters.group(2)
        security = wifi_parameters.group(3)
        if not ssid:
          ssid = 'Unknown'
        if not bssid:
          bssid = 'Unknown'
        if not security:
          security = 'Unknown'

        return (
            'New wifi configured. BSSID: {0:s}, SSID: {1:s}, '
            'Security: {2:s}.').format(bssid, ssid, security)

    return text

  def _GetTimeElementsTuple(self, key, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
        milliseconds (int): milliseconds.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    # TODO: what if time_elements_tuple is None.
    if key == 'turned_over_header':
      month, day, hours, minutes, seconds = time_elements_tuple

      milliseconds = 0
    else:
      _, month, day, hours, minutes, seconds, milliseconds = time_elements_tuple

    # Note that dfdatetime_time_elements.TimeElements will raise ValueError
    # for an invalid month.
    month = self._MONTH_DICT.get(month.lower(), 0)

    if month != 0 and month < self._last_month:
      # Gap detected between years.
      self._year_use += 1

    return self._year_use, month, day, hours, minutes, seconds, milliseconds

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
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    self._last_month = time_elements_tuple[1]

    function = self._GetValueFromStructure(structure, 'function')

    text = self._GetValueFromStructure(structure, 'text')
    if text:
      text = text.strip()

    event_data = MacWifiLogEventData()
    event_data.agent = self._GetValueFromStructure(structure, 'agent')
    event_data.function = function
    event_data.text = text

    if key == 'known_function_logline':
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
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseLogLine(parser_mediator, key, structure)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Mac Wifi log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    self._last_month = 0
    self._year_use = parser_mediator.GetEstimatedYear()

    key = 'header'

    try:
      structure = self._MAC_WIFI_HEADER.parseString(line)
    except pyparsing.ParseException:
      structure = None

    if not structure:
      key = 'turned_over_header'

      try:
        structure = self._MAC_WIFI_TURNED_OVER_HEADER.parseString(line)
      except pyparsing.ParseException:
        structure = None

    if not structure:
      logger.debug('Not a Mac Wifi log file')
      return False

    time_elements_tuple = self._GetTimeElementsTuple(key, structure)

    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logger.debug(
          'Not a Mac Wifi log file, invalid date and time: {0!s}'.format(
              time_elements_tuple))
      return False

    self._last_month = time_elements_tuple[1]

    return True


manager.ParsersManager.RegisterParser(MacWifiLogParser)
