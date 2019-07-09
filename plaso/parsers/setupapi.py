# -*- coding: utf-8 -*-
"""Parser for Windows Setupapi log files."""

from __future__ import unicode_literals

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class SetupapiLogEventData(events.EventData):
  """Setupapi log event data.

  Attributes:
    entry_type (str): log entry type such as "Device Install".
    end_time (str): date and time of the start of the log entry event.
    exit_status (str): the exit status of the entry.
  """

  DATA_TYPE = 'setupapi:log:line'

  def __init__(self):
    """Initializes event data."""
    super(SetupapiLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entry_type = None
    # TODO: Parse additional fields from the body of setupapi messages
    self.end_time = None
    self.exit_status = None


class SetupapiLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from Windows Setupapi log files."""

  NAME = 'setupapi'

  DESCRIPTION = 'Parser for Windows Setupapi log files.'

  _ENCODING = 'utf-8'

  # Increase the buffer size, as log messages can be very long.
  BUFFER_SIZE = 262144

  _SLASH = pyparsing.Literal('/').suppress()

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _THREE_DIGITS = text_parser.PyparsingConstants.THREE_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  _SETUPAPI_DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + _SLASH +
      _TWO_DIGITS + _SLASH +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS +
      pyparsing.Word('.,', exact=1).suppress() +
      _THREE_DIGITS
  )

  _SETUPAPI_LINE = (
      pyparsing.SkipTo('>>>  [', include=True).suppress() +
      pyparsing.SkipTo(']').setResultsName('entry_type') +
      pyparsing.SkipTo('>>>  Section start', include=True).suppress() +
      _SETUPAPI_DATE_TIME.setResultsName('start_time') +
      pyparsing.SkipTo('<<<  Section end ').setResultsName('message') +
      pyparsing.GoToColumn(17) +
      _SETUPAPI_DATE_TIME.setResultsName('end_time') +
      pyparsing.SkipTo('<<<  [Exit status: ', include=True).suppress() +
      pyparsing.SkipTo(']').setResultsName('exit_status') +
      pyparsing.SkipTo(pyparsing.lineEnd()) +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [
      ('logline', _SETUPAPI_LINE),
  ]

  def _ParseRecordLogline(self, parser_mediator, structure):
    """Parses a logline record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          log entry.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'start_time')
    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_structure)
      # Setupapi logs record in local time
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_structure))
      return

    time_zone = parser_mediator.timezone

    time_elements_structure = self._GetValueFromStructure(
        structure, 'end_time')
    # TODO: Convert to UTC
    end_time = ' '.join((
        '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}.{6:03d}'.format(
            *time_elements_structure),
        time_zone.zone))

    event_data = SetupapiLogEventData()
    event_data.entry_type = self._GetValueFromStructure(structure, 'entry_type')
    event_data.end_time = end_time
    event_data.exit_status = self._GetValueFromStructure(
        structure, 'exit_status')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED, time_zone=time_zone)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a log entry.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key != 'logline':
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseRecordLogline(parser_mediator, structure)

  def VerifyStructure(self, parser_mediator, lines):
    """Verify that this file is a Windows Setupapi log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._SETUPAPI_LINE.parseString(lines)
    except pyparsing.ParseException as exception:
      logger.debug('Not a Windows Setupapi log file: {0!s}'.format(exception))
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'start_time')

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_structure)
    except ValueError as exception:
      logger.debug((
          'Not a Windows Setupapi log file, invalid date/time: {0!s} '
          'with error: {1!s}').format(time_elements_structure, exception))
      return False

    if not date_time:
      logger.debug((
          'Not a Windows Setupapi log file, '
          'invalid date/time: {0!s}').format(time_elements_structure))
      return False

    return True


manager.ParsersManager.RegisterParser(SetupapiLogParser)
