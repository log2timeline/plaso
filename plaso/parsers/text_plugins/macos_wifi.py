# -*- coding: utf-8 -*-
"""Text parser plugin for MacOS Wi-Fi log (wifi.log) files."""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacOSWiFiLogEventData(events.EventData):
  """MacOS Wi-Fi log event data.

  Attributes:
    action (str): known Wi-Fi action, for example connected to an access point,
        configured, etc. If the action is not known, the value is the message
        of the log (text variable).
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    agent (str): name and identifier of process that generated the log message.
    function (str): name of function that generated the log message.
    text (str): log message.
  """

  DATA_TYPE = 'macos:wifi_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSWiFiLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.added_time = None
    self.agent = None
    self.function = None
    self.text = None


class MacOSWiFiLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin MacOS Wi-Fi log (wifi.log) files."""

  NAME = 'mac_wifi'
  DATA_FORMAT = 'MacOS Wi-Fi log (wifi.log) file'

  ENCODING = 'utf-8'

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

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
      _THREE_LETTERS.setResultsName('weekday') +
      _THREE_LETTERS.setResultsName('month') +
      _ONE_OR_TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') + pyparsing.Suppress('.') +
      _THREE_DIGITS.setResultsName('milliseconds'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Log line with a known function name.
  _KNOWN_FUNCTION_LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') + _AGENT +
      pyparsing.oneOf(_KNOWN_FUNCTIONS).setResultsName('function') +
      pyparsing.Literal(':') +
      pyparsing.restOfLine().setResultsName('text') +
      _END_OF_LINE)

  # Log line with an unknown function name.
  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') + pyparsing.NotAny(
          _AGENT +
          pyparsing.oneOf(_KNOWN_FUNCTIONS) +
          pyparsing.Literal(':')) +
      pyparsing.restOfLine().setResultsName('text') +
      _END_OF_LINE)

  _HEADER_LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('***Starting Up***').setResultsName('text') +
      _END_OF_LINE)

  _DATE_TIME_TURNED_OVER_HEADER = pyparsing.Group(
      _THREE_LETTERS.setResultsName('month') +
      _ONE_OR_TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds'))

  _TURNED_OVER_HEADER_LOG_LINE = (
      _DATE_TIME_TURNED_OVER_HEADER.setResultsName('date_time') +
      pyparsing.Combine(
          pyparsing.Word(pyparsing.printables) +
          pyparsing.Word(pyparsing.printables) +
          pyparsing.Literal('logfile turned over'),
          joinString=' ', adjacent=False).setResultsName('text') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('header_line', _HEADER_LOG_LINE),
      ('known_function_log_line', _KNOWN_FUNCTION_LOG_LINE),
      ('log_line', _LOG_LINE),
      ('turned_over_header_line', _TURNED_OVER_HEADER_LOG_LINE)]

  VERIFICATION_GRAMMAR = (
      _HEADER_LOG_LINE ^ _KNOWN_FUNCTION_LOG_LINE ^ _LOG_LINE ^
      _TURNED_OVER_HEADER_LOG_LINE)

  def _GetAction(self, action, text):
    """Parse the well known actions for easy reading.

    Args:
      action (str): the function or action called by the agent.
      text (str): text from a log line.

    Returns:
       str: a formatted string representing the known (or common) action.
           If the action is not known the original log text is returned.
    """
    # TODO: replace "x in y" checks by startswith if possible.
    if 'airportdProcessDLILEvent' in action:
      network_interface = text.split()[0]
      return 'Interface {0:s} turn up.'.format(network_interface)

    if 'doAutoJoin' in action:
      match = self._CONNECTED_RE.match(text)
      if match:
        ssid = match.group(1)[1:-1]
      else:
        ssid = 'Unknown'
      return 'Wi-Fi connected to SSID: {0:s}'.format(ssid)

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

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = MacOSWiFiLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.agent = self._GetValueFromStructure(structure, 'agent')
    event_data.function = self._GetValueFromStructure(structure, 'function')
    event_data.text = self._GetStringValueFromStructure(structure, 'text')

    if key == 'known_function_log_line':
      event_data.action = self._GetAction(event_data.function, event_data.text)

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      if len(time_elements_structure) == 5:
        month_string, day_of_month, hours, minutes, seconds = (
            time_elements_structure)

        milliseconds = None
      else:
        _, month_string, day_of_month, hours, minutes, seconds, milliseconds = (
            time_elements_structure)

      month = self._GetMonthFromString(month_string)

      self._UpdateYear(month)

      relative_year = self._GetRelativeYear()

      if milliseconds is None:
        time_elements_tuple = (
            relative_year, month, day_of_month, hours, minutes, seconds)

        date_time = dfdatetime_time_elements.TimeElements(
            is_delta=True, time_elements_tuple=time_elements_tuple)

      else:
        time_elements_tuple = (
            relative_year, month, day_of_month, hours, minutes, seconds,
            milliseconds)

        date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
            is_delta=True, time_elements_tuple=time_elements_tuple)

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._SetEstimatedYear(parser_mediator)

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(MacOSWiFiLogTextPlugin)
