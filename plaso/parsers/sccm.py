# -*_ coding: utf-8 -*-
"""Parser for SCCM Logs."""
import re

import pyparsing

from plaso.containers import text_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class SCCMLogEvent(text_events.TextEvent):
  """Object class to represent SCCM log events """

  DATA_TYPE = u'software_management:sccm:log'


class SCCMParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Windows System Center Configuration Manager (SCCM) logs."""

  NAME = u'sccm'
  DESCRIPTION = u'Parser for SCCM logs files.'

  _ENCODING = u'utf-8-sig'

  # Increasing the buffer size as SCCM messages are commonly well larger
  # than the default value.
  BUFFER_SIZE = 16384

  LINE_STRUCTURES = []

  _MICRO_SECONDS_PER_MINUTE = 60 * 1000000

  # PyParsing Components used to construct grammars for parsing lines.
  _PARSING_COMPONENTS = {
      u'msg_left_delimiter': pyparsing.Literal(u'<![LOG['),
      u'msg_right_delimiter': pyparsing.Literal(u']LOG]!><time="'),
      u'year': text_parser.PyparsingConstants.YEAR.setResultsName(u'year'),
      u'month': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.
                setResultsName(u'month'),
      u'day': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.
              setResultsName(u'day'),
      u'microsecond': pyparsing.Regex(r'\d{3,7}').
                      setResultsName(u'microsecond'),
      u'utc_offset_minutes': pyparsing.Regex(r'[-+]\d{3}').
                             setResultsName(u'utc_offset_minutes'),
      u'date_prefix': pyparsing.Literal(u'" date="').
                      setResultsName(u'date_prefix'),
      u'component_prefix': pyparsing.Literal(u'" component="').
                           setResultsName(u'component_prefix'),
      u'component': pyparsing.Word(pyparsing.alphanums).
                    setResultsName(u'component'),
      u'text': pyparsing.Regex(r'.*?(?=(]LOG]!><time="))', re.DOTALL).
               setResultsName(u'text'),
      u'line_remainder': pyparsing.Regex(r'.*?(?=(\<!\[LOG\[))', re.DOTALL).
                         setResultsName(u'line_remainder'),
      u'lastline_remainder': pyparsing.restOfLine.
                             setResultsName(u'lastline_remainder'),
      u'hour': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.
               setResultsName(u'hour'),
      u'minute': text_parser.PyparsingConstants.TWO_DIGITS.
                 setResultsName(u'minute'),
      u'second': text_parser.PyparsingConstants.TWO_DIGITS.
                 setResultsName(u'second')}

  # Base grammar for individual log event lines.
  LINE_GRAMMAR_BASE = (
      _PARSING_COMPONENTS[u'msg_left_delimiter'] +
      _PARSING_COMPONENTS[u'text'] +
      _PARSING_COMPONENTS[u'msg_right_delimiter'] +
      _PARSING_COMPONENTS[u'hour'] +
      pyparsing.Suppress(u':') + _PARSING_COMPONENTS[u'minute'] +
      pyparsing.Suppress(u':') + _PARSING_COMPONENTS[u'second'] +
      pyparsing.Suppress(u'.') + _PARSING_COMPONENTS[u'microsecond'] +
      _PARSING_COMPONENTS[u'date_prefix'] + _PARSING_COMPONENTS[u'month'] +
      pyparsing.Suppress(u'-') + _PARSING_COMPONENTS[u'day'] +
      pyparsing.Suppress(u'-') + _PARSING_COMPONENTS[u'year'] +
      _PARSING_COMPONENTS[u'component_prefix'] +
      _PARSING_COMPONENTS[u'component'])

  # Grammar for individual log event lines with a minutes offset from UTC.
  LINE_GRAMMAR_OFFSET = (
      _PARSING_COMPONENTS[u'msg_left_delimiter'] +
      _PARSING_COMPONENTS[u'text'] +
      _PARSING_COMPONENTS[u'msg_right_delimiter'] +
      _PARSING_COMPONENTS[u'hour'] +
      pyparsing.Suppress(u':') + _PARSING_COMPONENTS[u'minute'] +
      pyparsing.Suppress(u':') + _PARSING_COMPONENTS[u'second'] +
      pyparsing.Suppress(u'.') + _PARSING_COMPONENTS[u'microsecond'] +
      _PARSING_COMPONENTS[u'utc_offset_minutes'] +
      _PARSING_COMPONENTS[u'date_prefix'] + _PARSING_COMPONENTS[u'month'] +
      pyparsing.Suppress(u'-') + _PARSING_COMPONENTS[u'day'] +
      pyparsing.Suppress(u'-') + _PARSING_COMPONENTS[u'year'] +
      _PARSING_COMPONENTS[u'component_prefix'] +
      _PARSING_COMPONENTS[u'component'])

  LINE_STRUCTURES = [
      (u'log_entry',
       LINE_GRAMMAR_BASE + _PARSING_COMPONENTS[u'line_remainder']),
      (u'log_entry_at_end',
       LINE_GRAMMAR_BASE +_PARSING_COMPONENTS[u'lastline_remainder'] +
       pyparsing.lineEnd),
      (u'log_entry_offset',
       LINE_GRAMMAR_OFFSET + _PARSING_COMPONENTS[u'line_remainder']),
      (u'log_entry_offset_at_end',
       LINE_GRAMMAR_OFFSET + _PARSING_COMPONENTS[u'lastline_remainder'] +
       pyparsing.lineEnd)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return an SCCM log event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Raises:
      TimestampError: when a non-int value for microseconds is encountered.
    """
    # Sometimes, SCCM logs will exhibit a seven-digit sub-second precision
    # (100 nanosecond intervals). Using six-digit precision because
    # timestamps are in microseconds.
    if len(structure.microsecond) > 6:
      structure.microsecond = structure.microsecond[0:6]

    try:
      microseconds = int(structure.microsecond, 10)
    except ValueError as exception:
      parser_mediator.ProduceParseError(
          u'unable to determine microseconds with error: {0:s}'.format(
              exception))
      return

    # 3-digit precision is milliseconds,
    # so multiply by 1000 to convert to microseconds
    if len(structure.microsecond) == 3:
      microseconds *= 1000

    try:
      timestamp = timelib.Timestamp.FromTimeParts(
          structure.year, structure.month, structure.day,
          structure.hour, structure.minute, structure.second, microseconds)
    except errors.TimestampError as exception:
      timestamp = timelib.Timestamp.NONE_TIMESTAMP
      parser_mediator.ProduceParseError(
          u'unable to determine timestamp with error: {0:s}'.format(
              exception))

    # If an offset is given for the event, apply the offset to convert to UTC.
    if timestamp and u'offset' in key:
      try:
        delta_microseconds = int(structure.utc_offset_minutes[1:], 10)
      except (IndexError, ValueError) as exception:
        raise errors.TimestampError(
            u'Unable to parse minute offset from UTC with error: {0:s}.'.format(
                exception))

      delta_microseconds *= self._MICRO_SECONDS_PER_MINUTE
      if structure.utc_offset_minutes[0] == u'-':
        delta_microseconds = -delta_microseconds
      timestamp += delta_microseconds

    event_object = SCCMLogEvent(timestamp, 0, structure)
    parser_mediator.ProduceEvent(event_object)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies whether content corresponds to an SCCM log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      lines: A buffer containing lines from a log file.

    Returns:
      Returns a boolean that indicates the log lines appear to contain
      content from an SCCM log file.
    """
    # Identify the token to which we attempt a match.
    match = self._PARSING_COMPONENTS[u'msg_left_delimiter'].match

    # Because logs files can lead with a partial event,
    # we can't assume that the first character (post-BOM)
    # in the file is the beginning of our match - so we
    # look for match anywhere in lines.
    return match in lines


manager.ParsersManager.RegisterParser(SCCMParser)
