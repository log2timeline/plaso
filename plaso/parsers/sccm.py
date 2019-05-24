# -*_ coding: utf-8 -*-
"""Parser for SCCM Logs."""

from __future__ import unicode_literals

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
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

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _ONE_OR_TWO_DIGITS = text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS

  # PyParsing Components used to construct grammars for parsing lines.
  _PARSING_COMPONENTS = {
      'msg_left_delimiter': pyparsing.Literal('<![LOG['),
      'msg_right_delimiter': pyparsing.Literal(']LOG]!><time="'),
      'year': _FOUR_DIGITS.setResultsName('year'),
      'month': _ONE_OR_TWO_DIGITS.setResultsName('month'),
      'day': _ONE_OR_TWO_DIGITS.setResultsName('day'),
      'fraction_of_second': pyparsing.Regex(r'\d{3,7}').setResultsName(
          'fraction_of_second'),
      'utc_offset_minutes': pyparsing.Regex(r'[-+]\d{2,3}').setResultsName(
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
      pyparsing.Suppress('.') + _PARSING_COMPONENTS['fraction_of_second'] +
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
      pyparsing.Suppress('.') + _PARSING_COMPONENTS['fraction_of_second'] +
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

  def _GetISO8601String(self, structure):
    """Retrieves an ISO8601 date time string from the structure.

    The date and time values in the SCCM log are formatted as:
    time="19:33:19.766-330" date="11-28-2014"

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      str: ISO 8601 date time string.

    Raises:
      ValueError: if the structure cannot be converted into a date time string.
    """
    fraction_of_second = self._GetValueFromStructure(
        structure, 'fraction_of_second')
    fraction_of_second_length = len(fraction_of_second)
    if fraction_of_second_length not in (3, 6, 7):
      raise ValueError(
          'unsupported time fraction of second length: {0:d}'.format(
              fraction_of_second_length))

    try:
      fraction_of_second = int(fraction_of_second, 10)
    except (TypeError, ValueError) as exception:
      raise ValueError(
          'unable to determine fraction of second with error: {0!s}'.format(
              exception))

    # TODO: improve precision support, but for now ignore the 100ns precision.
    if fraction_of_second_length == 7:
      fraction_of_second, _ = divmod(fraction_of_second, 10)

    year = self._GetValueFromStructure(structure, 'year')
    month = self._GetValueFromStructure(structure, 'month')
    day_of_month = self._GetValueFromStructure(structure, 'day')
    hours = self._GetValueFromStructure(structure, 'hour')
    minutes = self._GetValueFromStructure(structure, 'minute')
    seconds = self._GetValueFromStructure(structure, 'second')

    date_time_string = '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}'.format(
        year, month, day_of_month, hours, minutes, seconds)

    if fraction_of_second_length > 0:
      date_time_string = '{0:s}.{1:d}'.format(
          date_time_string, fraction_of_second)

    utc_offset_minutes = self._GetValueFromStructure(
        structure, 'utc_offset_minutes')
    if utc_offset_minutes is not None:
      try:
        time_zone_offset = int(utc_offset_minutes[1:], 10)
      except (IndexError, ValueError) as exception:
        raise ValueError(
            'Unable to parse time zone offset with error: {0!s}.'.format(
                exception))

      time_zone_hours, time_zone_minutes = divmod(time_zone_offset, 60)
      date_time_string = '{0:s}{1:s}{2:02d}:{3:02d}'.format(
          date_time_string, utc_offset_minutes[0], time_zone_hours,
          time_zone_minutes)

    return date_time_string

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return an SCCM log event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in (
        'log_entry', 'log_entry_at_end', 'log_entry_offset',
        'log_entry_offset_at_end'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    try:
      date_time_string = self._GetISO8601String(structure)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to determine date time string with error: {0!s}'.format(
              exception))

    fraction_of_second = self._GetValueFromStructure(
        structure, 'fraction_of_second')
    fraction_of_second_length = len(fraction_of_second)
    if fraction_of_second_length == 3:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()
    elif fraction_of_second_length in (6, 7):
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromStringISO8601(date_time_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse date time value: {0:s} with error: {1!s}'.format(
              date_time_string, exception))
      return

    event_data = SCCMLogEventData()
    event_data.component = self._GetValueFromStructure(structure, 'component')
    # TODO: pass line number to offset or remove.
    event_data.offset = 0
    event_data.text = self._GetValueFromStructure(structure, 'text')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
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
