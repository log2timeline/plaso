# -*- coding: utf-8 -*-
"""Parser for iOS sysdiag log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class IOSSysdiagLogEventData(events.EventData):
  """iOS sysdiagnose log event data.

  Attributes:
    body (str): body of the event line.
    originating_call (str): call that created the entry.
    process_identifier (str): process_identifier.
    severity (str): severity of the message.
  """

  DATA_TYPE = 'ios:sysdiag:log:line'

  def __init__(self):
    """Initializes event data."""
    super(IOSSysdiagLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.originating_call = None
    self.process_identifier = None
    self.severity = None


class IOSSysdiagLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for iOS mobile installation log files."""

  NAME = 'ios_sysdiag_log'
  DATA_FORMAT = 'iOS sysdiag log'

  MONTHS = {
      'Jan': 1,
      'Feb': 2,
      'Mar': 3,
      'Apr': 4,
      'May': 5,
      'Jun': 6,
      'Jul': 7,
      'Aug': 8,
      'Sep': 9,
      'Oct': 10,
      'Nov': 11,
      'Dec': 12}

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  _TIMESTAMP = (
      _THREE_LETTERS.suppress() +
      _THREE_LETTERS.setResultsName('month') +
      _ONE_OR_TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') +
      _FOUR_DIGITS.setResultsName('year'))

  _ELEMENT_NUMBER = (
      pyparsing.Suppress('[') +
      pyparsing.Word(pyparsing.nums).setResultsName('process_identifier') +
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

  _BODY_END = pyparsing.StringEnd() | _TIMESTAMP

  _ELEMENT_BODY = (
      pyparsing.Optional(pyparsing.Suppress(pyparsing.Literal(': '))) +
      pyparsing.SkipTo(_BODY_END).setResultsName('body'))

  _LINE_GRAMMAR = (
      _TIMESTAMP + _ELEMENT_NUMBER + _ELEMENT_SEVERITY +
      _ELEMENT_ID + _ELEMENT_ORIGINATOR + _ELEMENT_BODY +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses an iOS mobile installation log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    month_string = self._GetValueFromStructure(structure, 'month')

    year = self._GetValueFromStructure(structure, 'year')
    month = self.MONTHS.get(month_string)
    day_of_month = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')

    event_data = IOSSysdiagLogEventData()
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
    event_data.severity = self._GetValueFromStructure(structure, 'severity')
    event_data.originating_call = self._GetValueFromStructure(
        structure, 'originating_call')
    event_data.body = self._GetValueFromStructure(structure, 'body')

    try:
      date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
          year, month, day_of_month, hours, minutes, seconds))
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is an iOS mobile installation log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
        parsers and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    match_generator = self._LINE_GRAMMAR.scanString(lines, maxMatches=1)
    return bool(list(match_generator))


manager.ParsersManager.RegisterParser(IOSSysdiagLogParser)
