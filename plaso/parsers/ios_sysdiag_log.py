# -*- coding: utf-8 -*-
"""Parser for iOS sysdiag log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


class IOSSysdiagLogEventData(events.EventData):
  """iOS sysdiagnose log event data.

  Attributes:
    body (str): body of the event line.
    originating_call (str): call that created the entry.
    process_identifier (str): process_identifier.
    severity (str): severity of the message.
    written_time (dfdatetime.DateTimeValues): date and time the log entry was
        written.
  """

  DATA_TYPE = 'ios:sysdiag_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSSysdiagLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.originating_call = None
    self.process_identifier = None
    self.severity = None
    self.written_time = None


class IOSSysdiagLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for iOS mobile installation log files."""

  NAME = 'ios_sysdiag_log'
  DATA_FORMAT = 'iOS sysdiag log'

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  # Date and time values are formatted as: Wed Aug 11 05:51:02 2021
  _DATE_TIME = (
      _THREE_LETTERS.suppress() + _THREE_LETTERS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _FOUR_DIGITS).setResultsName('date_time')

  _ELEMENT_NUMBER = (
      pyparsing.Suppress('[') + _INTEGER.setResultsName('process_identifier') +
      pyparsing.Suppress(']'))

  _ELEMENT_SEVERITY = (
      pyparsing.Suppress('<') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('severity') +
      pyparsing.Suppress('>'))

  _ELEMENT_ID = (
      pyparsing.Suppress('(') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('id') +
      pyparsing.Suppress(')'))

  _ELEMENT_ORIGINATOR = pyparsing.SkipTo(
      pyparsing.Literal(': ')).setResultsName('originating_call')

  _BODY_END = pyparsing.StringEnd() | _DATE_TIME

  _ELEMENT_BODY = (
      pyparsing.Optional(pyparsing.Suppress(pyparsing.Literal(': '))) +
      pyparsing.SkipTo(_BODY_END).setResultsName('body'))

  _LINE_GRAMMAR = (
      _DATE_TIME + _ELEMENT_NUMBER + _ELEMENT_SEVERITY +
      _ELEMENT_ID + _ELEMENT_ORIGINATOR + _ELEMENT_BODY +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  _LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = IOSSysdiagLogEventData()
    event_data.body = self._GetValueFromStructure(structure, 'body')
    event_data.originating_call = self._GetValueFromStructure(
        structure, 'originating_call')
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
    event_data.severity = self._GetValueFromStructure(structure, 'severity')
    event_data.written_time = self._ParseTimeElements(time_elements_structure)

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
      month_string, day_of_month, hours, minutes, seconds, year = (
          time_elements_structure)

      month = self._MONTH_DICT.get(month_string.lower(), 0)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    match_generator = self._LINE_GRAMMAR.scanString(
        text_reader.lines, maxMatches=1)
    return bool(list(match_generator))


manager.ParsersManager.RegisterParser(IOSSysdiagLogParser)
