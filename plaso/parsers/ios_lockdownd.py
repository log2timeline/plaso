# -*- coding: utf-8 -*-
"""Parser for iOS lockdown daemon log files (ios_lockdownd.log)."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


class IOSLockdowndLogData(events.EventData):
  """iOS lockdown daemon (lockdownd) log event data.

  Attributes:
    body (str): body of the log entry.
    process_identifier (int): identifier of the process making the request to
        lockdownd.
    written_time (dfdatetime.DateTimeValues): date and time the log entry was
        written.
  """

  DATA_TYPE = 'ios:lockdownd_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSLockdowndLogData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.process_identifier = None
    self.written_time = None


class IOSLockdowndLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for iOS lockdown daemon log files (ios_lockdownd.log)."""

  NAME = 'ios_lockdownd'
  DATA_FORMAT = 'iOS lockdown daemon log'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      text_parser.PyParseIntCast)

  # Date and time values are formatted as: MM/DD/YY hh:mm:ss:######
  # For example: 10/13/21 07:57:42.865446
  _DATE_TIME = (
      _TWO_DIGITS + pyparsing.Suppress('/') +
      _TWO_DIGITS + pyparsing.Suppress('/') + _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Word('.,', exact=1).suppress() + _SIX_DIGITS).setResultsName(
          'date_time')

  _PID = (pyparsing.Suppress('pid=') +
          _INTEGER.setResultsName('process_identifier'))

  _BODY_END = pyparsing.StringEnd() | _DATE_TIME

  _BODY = pyparsing.SkipTo(_BODY_END).setResultsName('body')

  _LINE_GRAMMAR = _DATE_TIME + _PID + _BODY + pyparsing.ZeroOrMore(
      pyparsing.lineEnd())

  LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

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
      month, day_of_month, year, hours, minutes, seconds, microseconds = (
          time_elements_structure)

      time_elements_tuple = (
          2000 + year, month, day_of_month, hours, minutes, seconds,
          microseconds)

      return dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    body = self._GetValueFromStructure(structure, 'body')

    event_data = IOSLockdowndLogData()
    event_data.body = body.replace('\n', '').strip(' ')
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
    event_data.written_time = self._ParseTimeElements(time_elements_structure)

    parser_mediator.ProduceEventData(event_data)

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


manager.ParsersManager.RegisterParser(IOSLockdowndLogParser)
