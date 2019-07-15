# -*- coding: utf-8 -*-
"""Parser for Advanced Packaging Tool (APT) History log files."""

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


class AptHistoryLogEventData(events.EventData):
  """APT History log event data.

  Attributes:
    requestor (str): user requesting the activity.
    error (str): reported error.
    packages (str): list of packages being affected.
  """

  DATA_TYPE = 'apt:history:line'

  def __init__(self):
    """Initializes event data."""
    super(AptHistoryLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.requestor = None
    self.error = None
    self.packages = None


class AptHistoryLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from APT History log files."""

  NAME = 'apthistory'

  DESCRIPTION = 'Parser for APT History log files.'

  _ENCODING = 'utf-8'

  # Increase the buffer size, as log messages can be very long.
  BUFFER_SIZE = 131072

  _HYPHEN = text_parser.PyparsingConstants.HYPHEN

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  _APTHISTORY_DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + _HYPHEN +
      _TWO_DIGITS + _HYPHEN +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS
  )

  _APTHISTORY_LINE = (
      pyparsing.ZeroOrMore(pyparsing.lineEnd()) +
      pyparsing.Word('Start-Date: ').suppress() +
      _APTHISTORY_DATE_TIME.setResultsName('start_date') +
      pyparsing.SkipTo('End-Date: ').setResultsName('message') +
      pyparsing.GoToColumn(10) +
      _APTHISTORY_DATE_TIME.setResultsName('end_date') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [('logline', _APTHISTORY_LINE)]

  def _ParseRecordLogline(self, parser_mediator, structure):
    """Parses a logline record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          log entry.
    """
    time_zone = parser_mediator.timezone
    time_elements_structure = self._GetValueFromStructure(
        structure, 'start_date')
    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_structure)
      # APT History logs store date and time values in local time.
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_structure))
      return

    event_data = AptHistoryLogEventData()

    message = self._GetValueFromStructure(structure, 'message')
    lines = message.split('\n')

    for line in lines:
      if 'Commandline:' in line:
        event_data.command = line
      if 'Error:' in line:
        event_data.error = line
      if 'Requested-By:' in line:
        event_data.requestor = line

    for line in lines:
      event_data.packages = line
      if 'Downgrade:' in line:
        event = time_events.DateTimeValuesEvent(
            date_time,
            definitions.TIME_DESCRIPTION_DOWNGRADE,
            time_zone=time_zone)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      if 'Purge:' in line or 'Remove:' in line:
        event = time_events.DateTimeValuesEvent(
            date_time,
            definitions.TIME_DESCRIPTION_DELETED,
            time_zone=time_zone)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      if 'Install:' in line:
        event = time_events.DateTimeValuesEvent(
            date_time,
            definitions.TIME_DESCRIPTION_INSTALLATION,
            time_zone=time_zone)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      if 'Upgrade:' in line:
        event = time_events.DateTimeValuesEvent(
            date_time,
            definitions.TIME_DESCRIPTION_UPDATE,
            time_zone=time_zone)
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
    """Verify that this file is an APT History log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._APTHISTORY_LINE.parseString(lines)
    except pyparsing.ParseException as exception:
      logger.debug('Not an APT History log file: {0!s}'.format(exception))
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'start_time')

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_structure)
    except ValueError as exception:
      logger.debug((
          'Not an APT History log file, invalid date/time: {0!s} '
          'with error: {1!s}').format(time_elements_structure, exception))
      return False

    if not date_time:
      logger.debug((
          'Not an APT History log file, '
          'invalid date/time: {0!s}').format(time_elements_structure))
      return False

    return True


manager.ParsersManager.RegisterParser(AptHistoryLogParser)
