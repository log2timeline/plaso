# -*- coding: utf-8 -*-
"""Parser for vsftpd Logs."""

from __future__ import unicode_literals

import calendar

import pyparsing
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import text_parser
from plaso.parsers import manager


class VsftpdEventData(events.EventData):
  """vsftpd Log event data.

  Attributes:
    text (str): vsftpd log message.
  """

  DATA_TYPE = 'vsftpd:log'

  def __init__(self):
    """Initializes event data."""
    super(VsftpdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.text = None


class VsftpdLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the vsftpd Log."""

  NAME = 'vsftpd'
  DESCRIPTION = 'Parser for vsftpd log files.'

  _DATETIME_ELEMENTS = (
    text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('day_of_week') +
    text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
    text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day_of_month') +
    text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
    text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
    text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('seconds') +
    text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName('year'))

  # Note that the whitespace is suppressed by pyparsing.
  _DATE_TIME = pyparsing.Group(_DATETIME_ELEMENTS)

  _LOG_LINE = (
    _DATE_TIME.setResultsName('date_time') +
    pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  LINE_STRUCTURES = [
    ('logline', _LOG_LINE),
  ]

  def _get_time_elements_tuple(self, structure):
    """Pulls datetime information from data_time structure and returns tuple for dfdatetime.time_elements"""

    year = self._GetValueFromStructure(structure, 'year')
    month = list(calendar.month_abbr).index(self._GetValueFromStructure(structure, 'month'))
    day_of_month = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')

    return (year, month, day_of_month, hours, minutes, seconds)


  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfvfs.
        structure (pyparsing.ParseResults): structure of tokens derived from
            a line of a text file.
    """
    time_elements_tuple = self._get_time_elements_tuple(self._GetValueFromStructure(structure, 'date_time'))
    try:
        date_time = dfdatetime_time_elements.TimeElements(
            time_elements_tuple=time_elements_tuple)
        date_time.is_local_time = True
    except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid date time value: {0!s}'.format(time_elements_tuple))
        return

    event_data = VsftpdEventData()
    event_data.text = self._GetValueFromStructure(structure, 'text')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfvfs.
        key (str): identifier of the structure of tokens.
        structure (pyparsing.ParseResults): structure of tokens derived from
            a line of a text file.

    Raises:
        ParseError: when the structure type is unknown.
    """
    if key != 'logline':
        raise errors.ParseError(
            'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseLogLine(parser_mediator, structure)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Sophos Anti-Virus log file.

    Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfVFS.
        line (str): line from a text file.

    Returns:
        bool: True if the line is in the expected format, False if not.
    """
    try:
        structure = self._LOG_LINE.parseString(line)
    except pyparsing.ParseException:
        logger.debug('Not a vsftpd log file')
        return False

    time_elements_tuple = self._get_time_elements_tuple(self._GetValueFromStructure(structure, 'date_time'))
    try:
        dfdatetime_time_elements.TimeElements(
            time_elements_tuple=time_elements_tuple)
    except ValueError:
        logger.debug((
            'Not a vsftpd log file, invalid date and time: '
            '{0!s}').format(time_elements_tuple))
        return False

    return True


manager.ParsersManager.RegisterParser(VsftpdLogParser)
