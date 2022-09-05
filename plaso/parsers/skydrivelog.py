# -*- coding: utf-8 -*-
"""This file contains SkyDrive log file parser in plaso."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class SkyDriveLogEventData(events.EventData):
  """SkyDrive log event data.

  Attributes:
    detail (str): details.
    log_level (str): log level.
    module (str): name of the module that generated the log message.
    source_code (str): source file and line number that generated the log
        message.
  """

  DATA_TYPE = 'skydrive:log:line'

  def __init__(self):
    """Initializes event data."""
    super(SkyDriveLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.detail = None
    self.log_level = None
    self.module = None
    self.source_code = None


class SkyDriveLog2Parser(text_parser.PyparsingMultiLineTextParser):
  """Parses SkyDrive log files."""

  NAME = 'skydrive_log'
  DATA_FORMAT = 'OneDrive (or SkyDrive) log file'

  _ENCODING = 'utf-8'

  # Common SDF (SkyDrive Format) structures.
  _COMMA = pyparsing.Literal(',').suppress()
  _HYPHEN = text_parser.PyparsingConstants.HYPHEN

  _THREE_DIGITS = text_parser.PyparsingConstants.THREE_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  MSEC = pyparsing.Word(pyparsing.nums, max=3).setParseAction(
      text_parser.PyParseIntCast)
  IGNORE_FIELD = pyparsing.CharsNotIn(',').suppress()

  # Date and time format used in the header is: YYYY-MM-DD-hhmmss.###
  # For example: 2013-07-25-160323.291
  _SDF_HEADER_DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.DATE_ELEMENTS + _HYPHEN +
      _TWO_DIGITS.setResultsName('hours') +
      _TWO_DIGITS.setResultsName('minutes') +
      _TWO_DIGITS.setResultsName('seconds') +
      pyparsing.Literal('.').suppress() +
      _THREE_DIGITS.setResultsName('milliseconds')).setResultsName(
          'header_date_time')

  # Date and time format used in lines other than the header is:
  # MM-DD-YY,hh:mm:ss.###
  # For example: 07-25-13,16:06:31.820
  _SDF_DATE_TIME = (
      _TWO_DIGITS.setResultsName('month') + _HYPHEN +
      _TWO_DIGITS.setResultsName('day') + _HYPHEN +
      _TWO_DIGITS.setResultsName('year') + _COMMA +
      text_parser.PyparsingConstants.TIME_ELEMENTS + pyparsing.Suppress('.') +
      _THREE_DIGITS.setResultsName('milliseconds')).setResultsName(
          'date_time')

  _SDF_HEADER_START = (
      pyparsing.Literal('######').suppress() +
      pyparsing.Literal('Logging started.').setResultsName('log_start'))

  # Multiline entry end marker, matched from right to left.
  _SDF_ENTRY_END = pyparsing.StringEnd() | _SDF_HEADER_START | _SDF_DATE_TIME

  _SDF_LINE = (
      _SDF_DATE_TIME + _COMMA +
      IGNORE_FIELD + _COMMA + IGNORE_FIELD + _COMMA + IGNORE_FIELD + _COMMA +
      pyparsing.CharsNotIn(',').setResultsName('module') + _COMMA +
      pyparsing.CharsNotIn(',').setResultsName('source_code') + _COMMA +
      IGNORE_FIELD + _COMMA + IGNORE_FIELD + _COMMA +
      pyparsing.CharsNotIn(',').setResultsName('log_level') + _COMMA +
      pyparsing.SkipTo(_SDF_ENTRY_END).setResultsName('detail') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  _SDF_HEADER = (
      _SDF_HEADER_START +
      pyparsing.Literal('Version=').setResultsName('version_string') +
      pyparsing.Word(pyparsing.nums + '.').setResultsName('version_number') +
      pyparsing.Literal('StartSystemTime:').suppress() +
      _SDF_HEADER_DATE_TIME +
      pyparsing.Literal('StartLocalTime:').setResultsName(
          'local_time_string') +
      pyparsing.SkipTo(pyparsing.lineEnd()).setResultsName('details') +
      pyparsing.lineEnd())

  LINE_STRUCTURES = [
      ('logline', _SDF_LINE),
      ('header', _SDF_HEADER)]

  def _ParseHeader(self, parser_mediator, structure):
    """Parse header lines and store appropriate attributes.

    ['Logging started.', 'Version=', '17.0.2011.0627',
    [2013, 7, 25], 16, 3, 23, 291, 'StartLocalTime', '<details>']

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetValueFromStructure(
        structure, 'header_date_time')
    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    details = self._GetValueFromStructure(structure, 'details')
    local_time_string = self._GetValueFromStructure(
        structure, 'local_time_string')
    log_start = self._GetValueFromStructure(structure, 'log_start')
    version_number = self._GetValueFromStructure(structure, 'version_number')
    version_string = self._GetValueFromStructure(structure, 'version_string')

    event_data = SkyDriveLogEventData()
    # TODO: refactor detail to individual event data attributes.
    event_data.detail = '{0!s} {1!s} {2!s} {3!s} {4!s}'.format(
        log_start, version_string, version_number, local_time_string, details)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseLine(self, parser_mediator, structure):
    """Parses a logline and store appropriate attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    # TODO: what if time elements tuple is None.
    # TODO: Verify if date and time value is locale dependent.
    month, day_of_month, year, hours, minutes, seconds, milliseconds = (
        time_elements_tuple)

    year += 2000
    time_elements_tuple = (
        year, month, day_of_month, hours, minutes, seconds, milliseconds)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    # Replace newlines with spaces in structure.detail to preserve output.
    # TODO: refactor detail to individual event data attributes.
    detail = self._GetValueFromStructure(structure, 'detail')
    if detail:
      detail = detail.replace('\n', ' ').strip(' ')

    event_data = SkyDriveLogEventData()
    event_data.detail = detail
    event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
    event_data.module = self._GetValueFromStructure(structure, 'module')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in ('header', 'logline'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      self._ParseLine(parser_mediator, structure)

    elif key == 'header':
      self._ParseHeader(parser_mediator, structure)

  def VerifyStructure(self, parser_mediator, lines):
    """Verify that this file is a SkyDrive log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._SDF_HEADER.parseString(lines)
    except pyparsing.ParseException:
      logger.debug('Not a SkyDrive log file')
      return False

    time_elements_tuple = self._GetValueFromStructure(
        structure, 'header_date_time')
    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logger.debug(
          'Not a SkyDrive log file, invalid date and time: {0!s}'.format(
              time_elements_tuple))
      return False

    return True


manager.ParsersManager.RegisterParser(SkyDriveLog2Parser)
