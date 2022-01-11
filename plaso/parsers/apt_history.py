# -*- coding: utf-8 -*-
"""Parser for Advanced Packaging Tool (APT) History log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class APTHistoryLogEventData(events.EventData):
  """APT History log event data.

  Attributes:
    command (str): command executed
    error (str): reported error.
    packages (str): list of packages being affected.
    requester (str): user requesting the activity.
  """

  DATA_TYPE = 'apt:history:line'

  def __init__(self):
    """Initializes event data."""
    super(APTHistoryLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.error = None
    self.packages = None
    self.requester = None


class APTHistoryLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses for Advanced Packaging Tool (APT) History log files."""

  NAME = 'apt_history'

  DATA_FORMAT = 'Advanced Packaging Tool (APT) History log file'

  # APT History log lines can be very long.
  MAX_LINE_LENGTH = 65536

  _ENCODING = 'utf-8'

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

  _RECORD_START = (
      # APT History logs may start with empty lines
      pyparsing.ZeroOrMore(pyparsing.lineEnd()) +
      pyparsing.Literal('Start-Date:') +
      _APTHISTORY_DATE_TIME.setResultsName('start_date') +
      pyparsing.lineEnd())

  _RECORD_BODY = (
      pyparsing.MatchFirst([
          pyparsing.Literal('Commandline:'),
          pyparsing.Literal('Downgrade:'),
          pyparsing.Literal('Error:'),
          pyparsing.Literal('Install:'),
          pyparsing.Literal('Purge:'),
          pyparsing.Literal('Remove:'),
          pyparsing.Literal('Requested-By:'),
          pyparsing.Literal('Upgrade:')]) +
      pyparsing.restOfLine())

  _RECORD_END = (
      pyparsing.Literal('End-Date:') +
      _APTHISTORY_DATE_TIME.setResultsName('end_date') +
      pyparsing.OneOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [
      ('record_start', _RECORD_START),
      ('record_body', _RECORD_BODY),
      ('record_end', _RECORD_END)]

  def __init__(self):
    """Initializes an APT History parser."""
    super(APTHistoryLogParser, self).__init__()
    self._date_time = None
    self._event_data = None
    self._downgrade = None
    self._install = None
    self._purge = None
    self._remove = None
    self._upgrade = None

  @staticmethod
  def _BuildDateTime(time_elements_structure):
    """Builds time elements from an APT History time stamp.

    Args:
      time_elements_structure (pyparsing.ParseResults): structure of tokens
          derived from an APT History time stamp.

    Returns:
      dfdatetime.TimeElements: date and time extracted from the structure or
          None f the structure does not represent a valid string.
    """
    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exist.
    try:
      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
          year, month, day_of_month, hours, minutes, seconds))

      # APT History logs store date and time values in local time.
      date_time.is_local_time = True
      return date_time
    except (TypeError, ValueError):
      return None

  def _ParseRecordStart(self, parser_mediator, structure):
    """Parses the first line of a log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a log entry.
    """
    self._date_time = self._BuildDateTime(structure.get('start_date', None))
    if not self._date_time:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(self._date_time))
      return

    self._event_data = APTHistoryLogEventData()
    return

  def _ParseRecordBody(self, structure):
    """Parses a line from the body of a log record.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a log entry.

    Raises:
      ParseError: when the date and time value is missing.
    """
    if not self._date_time:
      raise errors.ParseError('Missing date time value.')

    # Command data
    if structure[0] == 'Commandline:':
      self._event_data.command = ''.join(structure)

    elif structure[0] == 'Error:':
      self._event_data.error = ''.join(structure)

    elif structure[0] == 'Requested-By:':
      self._event_data.requester = ''.join(structure)

    # Package lists
    elif structure[0] == 'Downgrade:':
      self._downgrade = ''.join(structure)

    elif structure[0] == 'Install:':
      self._install = ''.join(structure)

    elif structure[0] == 'Purge:':
      self._purge = ''.join(structure)

    elif structure[0] == 'Remove:':
      self._remove = ''.join(structure)

    elif structure[0] == 'Upgrade:':
      self._upgrade = ''.join(structure)

  def _ParseRecordEnd(self, parser_mediator):
    """Parses the last line of a log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.

    Raises:
      ParseError: when the date and time value is missing.
    """
    if not self._date_time:
      raise errors.ParseError('Missing date time value.')

    # Create relevant events for record
    if self._downgrade:
      self._event_data.packages = self._downgrade
      event = time_events.DateTimeValuesEvent(
          self._date_time,
          definitions.TIME_DESCRIPTION_DOWNGRADE,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, self._event_data)

    if self._install:
      self._event_data.packages = self._install
      event = time_events.DateTimeValuesEvent(
          self._date_time,
          definitions.TIME_DESCRIPTION_INSTALLATION,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, self._event_data)

    if self._purge:
      self._event_data.packages = self._purge
      event = time_events.DateTimeValuesEvent(
          self._date_time,
          definitions.TIME_DESCRIPTION_DELETED,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, self._event_data)

    if self._remove:
      self._event_data.packages = self._remove
      event = time_events.DateTimeValuesEvent(
          self._date_time,
          definitions.TIME_DESCRIPTION_DELETED,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, self._event_data)

    if self._upgrade:
      self._event_data.packages = self._upgrade
      event = time_events.DateTimeValuesEvent(
          self._date_time,
          definitions.TIME_DESCRIPTION_UPDATE,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, self._event_data)

  def _ResetState(self):
    """Resets stored values in the parser."""
    self._date_time = None
    self._downgrade = None
    self._event_data = None
    self._install = None
    self._purge = None
    self._remove = None
    self._upgrade = None

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
    if key == 'record_start':
      self._ParseRecordStart(parser_mediator, structure)
      return

    if key == 'record_body':
      self._ParseRecordBody(structure)
      return

    if key == 'record_end':
      self._ParseRecordEnd(parser_mediator)
      # Reset for next record.
      self._ResetState()
      return

    raise errors.ParseError(
        'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is an APT History log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): single line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      self._RECORD_START.parseString(line)
      # Reset stored values for parsing a new file.
      self._ResetState()
    except pyparsing.ParseException as exception:
      logger.debug('Not an APT History log file: {0!s}'.format(exception))
      return False

    return True


manager.ParsersManager.RegisterParser(APTHistoryLogParser)
