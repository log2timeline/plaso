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


class AptHistoryLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parses events from APT History log files."""

  NAME = 'apt_history'

  DESCRIPTION = 'Parser for APT History log files.'

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
    super(AptHistoryLogParser, self).__init__()
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
      dfdatetime.TimeElements: date and time extracted from the value or None
          if the value does not represent a valid string.
    """
    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_structure)
      # APT History logs store date and time values in local time.
      date_time.is_local_time = True
      return date_time
    except ValueError:
      return None

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
      time_elements_structure = self._GetValueFromStructure(
          structure, 'start_date')
      self._date_time = self._BuildDateTime(time_elements_structure)
      if not self._date_time:
        parser_mediator.ProduceExtractionWarning(
            'invalid date time value: {0!s}'.format(time_elements_structure))
        return

      self._event_data = AptHistoryLogEventData()
      return

    if key == 'record_body':
      if not self._date_time:
        raise errors.ParseError('Unable to parse, record incomplete.')

      # Command data
      if structure[0] == 'Commandline:':
        self._event_data.command = ''.join(structure)
        return
      if structure[0] == 'Error:':
        self._event_data.error = ''.join(structure)
        return
      if structure[0] == 'Requested-By:':
        self._event_data.requestor = ''.join(structure)
        return

      # Package lists
      if structure[0] == 'Downgrade:':
        self._downgrade = ''.join(structure)
        return
      if structure[0] == 'Install:':
        self._install = ''.join(structure)
        return
      if structure[0] == 'Purge:':
        self._purge = ''.join(structure)
        return
      if structure[0] == 'Remove:':
        self._remove = ''.join(structure)
        return
      if structure[0] == 'Upgrade:':
        self._upgrade = ''.join(structure)
        return

      return

    if key == 'record_end':
      if not self._date_time:
        raise errors.ParseError('Unable to parse, record incomplete.')

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

      # Reset for next record
      self._date_time = None
      self._event_data = None
      self._downgrade = None
      self._install = None
      self._purge = None
      self._remove = None
      self._upgrade = None

      return
    return

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
    except pyparsing.ParseException as exception:
      logger.debug('Not an APT History log file: {0!s}'.format(exception))
      return False

    return True


manager.ParsersManager.RegisterParser(AptHistoryLogParser)
