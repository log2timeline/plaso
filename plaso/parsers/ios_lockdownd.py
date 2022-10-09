# -*- coding: utf-8 -*-
"""Parser for iOS lockdown daemon log files (ios_lockdownd.log)."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class IOSLockdownLogData(events.EventData):
  """iOS lockdownd event data.

  Attributes:
    body (str): body of the event line.
    process_identifier (str): process making the request to lockdownd.
  """

  DATA_TYPE = 'ios:lockdown:log:line'

  def __init__(self):
    """Initializes iOS lockdown daemon log event data."""
    super(IOSLockdownLogData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.process_identifier = None


class IOSLockdownParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for iOS lockdown daemon log files (ios_lockdownd.log)."""

  NAME = 'ios_lockdownd'
  DATA_FORMAT = 'iOS lockdown daemon log'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _DATE_TIME = (
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('/') +
      _TWO_DIGITS.setResultsName('day_of_month') + pyparsing.Suppress('/') +
      _TWO_DIGITS.setResultsName('two_digit_year') +
      text_parser.PyparsingConstants.TIME_ELEMENTS +
      pyparsing.Word('.,', exact=1).suppress() +
      _INTEGER.setResultsName('microseconds'))

  _PID = (
      pyparsing.Suppress('pid=') +
      pyparsing.Word(pyparsing.nums).setResultsName('process_identifier'))

  _BODY_END = pyparsing.StringEnd() | _DATE_TIME

  _BODY = pyparsing.SkipTo(_BODY_END).setResultsName('body')

  _LINE_GRAMMAR = _DATE_TIME + _PID + _BODY + pyparsing.ZeroOrMore(
      pyparsing.lineEnd())

  LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

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

    year = self._GetValueFromStructure(structure, 'two_digit_year')
    month = self._GetValueFromStructure(structure, 'month')
    day = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')
    microseconds = self._GetValueFromStructure(structure, 'microseconds')

    body = self._GetValueFromStructure(structure, 'body')

    event_data = IOSLockdownLogData()
    event_data.body = body.replace('\n', '').strip(' ')
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')

    try:
      time_elements_tuple = (
          2000 + year, month, day, hours, minutes, seconds, microseconds)
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported date time value')
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is an iOS lockdown daemon log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfVFS.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    match_generator = self._LINE_GRAMMAR.scanString(lines, maxMatches=1)
    return bool(list(match_generator))


manager.ParsersManager.RegisterParser(IOSLockdownParser)
