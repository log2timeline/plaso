# -*- coding: utf-8 -*-
"""Parser for vsftpd Logs."""

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
  """Parses a vsftpd log."""

  NAME = 'vsftpd'
  DATA_FORMAT = 'vsftpd log file'

  _DATETIME_ELEMENTS = (
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('day') +
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          'day_of_month') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('hours') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('minutes') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('seconds') +
      text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName('year'))

  # Whitespace is suppressed by pyparsing.
  _DATE_TIME = pyparsing.Group(_DATETIME_ELEMENTS)

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  LINE_STRUCTURES = [
      ('logline', _LOG_LINE),
  ]

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
        structure (pyparsing.ParseResults): structure of tokens derived from
            a line of a vsftp log file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    _, month, day_of_month, hours, minutes, seconds, year = time_elements_tuple
    month = self._MONTH_DICT.get(month.lower(), 0)
    return (year, month, day_of_month, hours, minutes, seconds)


  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfvfs.
        structure (pyparsing.ParseResults): structure of tokens derived from
            a line of a text file.
    """
    time_elements_tuple = self._GetTimeElementsTuple(structure)
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
    """Verify that this file is a vsftpd log file.

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
      return False

    if (' [pid ' not in line) or (': Client ' not in line):
      return False

    time_elements_tuple = self._GetTimeElementsTuple(structure)
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
