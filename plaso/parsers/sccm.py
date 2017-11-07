# -*_ coding: utf-8 -*-
"""Parser for SCCM Logs."""

from __future__ import unicode_literals

import re

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class SCCMLogEventData(events.EventData):
  """SCCM log event data.

  Attributes:
    component (str): component.
    text (str): text.
  """

  DATA_TYPE = 'software_management:sccm:log'

  def __init__(self):
    """Initializes event data."""
    super(SCCMLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.component = None
    self.text = None


class SCCMParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Windows System Center Configuration Manager (SCCM) logs."""

  NAME = 'sccm'
  DESCRIPTION = 'Parser for SCCM logs files.'

  _ENCODING = 'utf-8-sig'

  # Increasing the buffer size as SCCM messages are commonly well larger
  # than the default value.
  BUFFER_SIZE = 16384

  LINE_STRUCTURES = []

  _MICRO_SECONDS_PER_MINUTE = 60 * 1000000

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _ONE_OR_TWO_DIGITS = text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS

  # PyParsing Components used to construct grammars for parsing lines.
  _PARSING_COMPONENTS = {
      'msg_left_delimiter': pyparsing.Literal('<![LOG['),
      'msg_right_delimiter': pyparsing.Literal(']LOG]!><time="'),
      'year': _FOUR_DIGITS.setResultsName('year'),
      'month': _ONE_OR_TWO_DIGITS.setResultsName('month'),
      'day': _ONE_OR_TWO_DIGITS.setResultsName('day'),
      'microsecond': pyparsing.Regex(r'\d{3,7}'). setResultsName('microsecond'),
      'utc_offset_minutes': pyparsing.Regex(r'[-+]\d{3}').setResultsName(
          'utc_offset_minutes'),
      'date_prefix': pyparsing.Literal('" date="'). setResultsName(
          'date_prefix'),
      'component_prefix': pyparsing.Literal('" component="').setResultsName(
          'component_prefix'),
      'component': pyparsing.Word(pyparsing.alphanums).setResultsName(
          'component'),
      'text': pyparsing.Regex(
          r'.*?(?=(]LOG]!><time="))', re.DOTALL).setResultsName('text'),
      'line_remainder': pyparsing.Regex(
          r'.*?(?=(\<!\[LOG\[))', re.DOTALL).setResultsName('line_remainder'),
      'lastline_remainder': pyparsing.restOfLine.setResultsName(
          'lastline_remainder'),
      'hour': _ONE_OR_TWO_DIGITS.setResultsName('hour'),
      'minute': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'minute'),
      'second': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'second')}

  # Base grammar for individual log event lines.
  LINE_GRAMMAR_BASE = (
      _PARSING_COMPONENTS['msg_left_delimiter'] +
      _PARSING_COMPONENTS['text'] +
      _PARSING_COMPONENTS['msg_right_delimiter'] +
      _PARSING_COMPONENTS['hour'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['minute'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['second'] +
      pyparsing.Suppress('.') + _PARSING_COMPONENTS['microsecond'] +
      _PARSING_COMPONENTS['date_prefix'] + _PARSING_COMPONENTS['month'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['day'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['year'] +
      _PARSING_COMPONENTS['component_prefix'] +
      _PARSING_COMPONENTS['component'])

  # Grammar for individual log event lines with a minutes offset from UTC.
  LINE_GRAMMAR_OFFSET = (
      _PARSING_COMPONENTS['msg_left_delimiter'] +
      _PARSING_COMPONENTS['text'] +
      _PARSING_COMPONENTS['msg_right_delimiter'] +
      _PARSING_COMPONENTS['hour'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['minute'] +
      pyparsing.Suppress(':') + _PARSING_COMPONENTS['second'] +
      pyparsing.Suppress('.') + _PARSING_COMPONENTS['microsecond'] +
      _PARSING_COMPONENTS['utc_offset_minutes'] +
      _PARSING_COMPONENTS['date_prefix'] + _PARSING_COMPONENTS['month'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['day'] +
      pyparsing.Suppress('-') + _PARSING_COMPONENTS['year'] +
      _PARSING_COMPONENTS['component_prefix'] +
      _PARSING_COMPONENTS['component'])

  LINE_STRUCTURES = [
      ('log_entry',
       LINE_GRAMMAR_BASE + _PARSING_COMPONENTS['line_remainder']),
      ('log_entry_at_end',
       LINE_GRAMMAR_BASE +_PARSING_COMPONENTS['lastline_remainder'] +
       pyparsing.lineEnd),
      ('log_entry_offset',
       LINE_GRAMMAR_OFFSET + _PARSING_COMPONENTS['line_remainder']),
      ('log_entry_offset_at_end',
       LINE_GRAMMAR_OFFSET + _PARSING_COMPONENTS['lastline_remainder'] +
       pyparsing.lineEnd)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return an SCCM log event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
      TimestampError: when a non-int value for microseconds is encountered.
    """
    if key not in (
        'log_entry', 'log_entry_at_end', 'log_entry_offset',
        'log_entry_offset_at_end'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    # Sometimes, SCCM logs will exhibit a seven-digit sub-second precision
    # (100 nanosecond intervals). Using six-digit precision because
    # timestamps are in microseconds.
    if len(structure.microsecond) > 6:
      structure.microsecond = structure.microsecond[0:6]

    try:
      microseconds = int(structure.microsecond, 10)
    except ValueError as exception:
      parser_mediator.ProduceExtractionError(
          'unable to determine microseconds with error: {0!s}'.format(
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
      parser_mediator.ProduceExtractionError(
          'unable to determine timestamp with error: {0!s}'.format(
              exception))

    # If an offset is given for the event, apply the offset to convert to UTC.
    if timestamp and 'offset' in key:
      try:
        delta_microseconds = int(structure.utc_offset_minutes[1:], 10)
      except (IndexError, ValueError) as exception:
        raise errors.TimestampError(
            'Unable to parse minute offset from UTC with error: {0!s}.'.format(
                exception))

      delta_microseconds *= self._MICRO_SECONDS_PER_MINUTE
      if structure.utc_offset_minutes[0] == '-':
        delta_microseconds = -delta_microseconds
      timestamp += delta_microseconds

    event_data = SCCMLogEventData()
    event_data.component = structure.component
    # TODO: pass line number to offset or remove.
    event_data.offset = 0
    event_data.text = structure.text

    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies whether content corresponds to an SCCM log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    # Identify the token to which we attempt a match.
    match = self._PARSING_COMPONENTS['msg_left_delimiter'].match

    # Because logs files can lead with a partial event,
    # we can't assume that the first character (post-BOM)
    # in the file is the beginning of our match - so we
    # look for match anywhere in lines.
    return match in lines


manager.ParsersManager.RegisterParser(SCCMParser)
