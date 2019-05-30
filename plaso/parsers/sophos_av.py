# -*- coding: utf-8 -*-
"""Sophos Anti-Virus log (SAV.txt) parser.

References
https://community.sophos.com/kb/en-us/110923
"""

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


class SophosAVLogEventData(events.EventData):
  """Sophos Anti-Virus log event data.

  Attributes:
    text (str): Sophos Anti-Virus log message.
  """

  DATA_TYPE = 'sophos:av:log'

  def __init__(self):
    """Initializes event data."""
    super(SophosAVLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.text = None


class SophosAVLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses Anti-Virus logs (SAV.txt) files."""

  NAME = 'sophos_av'
  DESCRIPTION = 'Parser for Anti-Virus log (SAV.txt) files.'

  _ENCODING = 'utf-16-le'

  MAX_LINE_LENGTH = 4096

  _DATE_ELEMENTS = (
      text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName('year') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('month') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('day_of_month'))
  _TIME_ELEMENTS = (
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('hours') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('minutes') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('seconds'))

  # Note that the whitespace is suppressed by pyparsing.
  _DATE_TIME = pyparsing.Group(_DATE_ELEMENTS + _TIME_ELEMENTS)

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  LINE_STRUCTURES = [
      ('logline', _LOG_LINE),
  ]

  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      # TODO: check if date and time values are local time or in UTC.
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = SophosAVLogEventData()
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
      logger.debug('Not a Sophos Anti-Virus log file')
      return False

    # Expect spaces at position 9 and 16.
    if ' ' not in (line[8], line[15]):
      logger.debug('Not a Sophos Anti-Virus log file')
      return False

    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    try:
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logger.debug((
          'Not a Sophos Anti-Virus log file, invalid date and time: '
          '{0!s}').format(time_elements_tuple))
      return False

    return True


manager.ParsersManager.RegisterParser(SophosAVLogParser)
