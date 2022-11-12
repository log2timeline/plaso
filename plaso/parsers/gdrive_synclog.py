# -*- coding: utf-8 -*-
"""Parser for Google Drive Sync log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class GoogleDriveSyncLogEventData(events.EventData):
  """Google Drive Sync log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    level (str): logging level of event such as "DEBUG", "WARN", "INFO" and
        "ERROR".
    message (str): log message.
    process_identifier (int): process identifier of process which logged event.
    source_code (str): filename:line_number of source file which logged event.
    thread (str): colon-separated thread identifier in the form "ID:name"
        which logged event.
  """

  DATA_TYPE = 'gdrive_sync:log:line'
  DATA_TYPE = 'google_drive_sync_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSyncLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.level = None
    self.message = None
    self.process_identifier = None
    self.source_code = None
    self.thread = None


class GoogleDriveSyncLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from Google Drive Sync log files."""

  NAME = 'gdrive_synclog'
  DATA_FORMAT = 'Google Drive Sync log file'

  _ENCODING = 'utf-8'

  # Increase the buffer size, as log messages are often many lines of Python
  # object dumps or similar. The default is too small for this and results in
  # premature end of string matching on multi-line log entries.
  BUFFER_SIZE = 16384

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _FRACTION_OF_SECOND = pyparsing.Word('.,', exact=1).suppress() + _THREE_DIGITS

  _TIME_ZONE_OFFSET = pyparsing.Group(
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS +
      _FRACTION_OF_SECOND +
      _TIME_ZONE_OFFSET).setResultsName('date_time')

  _PROCESS_IDENTIFIER = (
      pyparsing.Suppress('pid=') +
      _INTEGER.setResultsName('process_identifier'))

  _THREAD = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.printables))

  # Multiline entry end marker, matched from right to left.
  _GDS_ENTRY_END = pyparsing.StringEnd() | _DATE_TIME

  _GDS_LINE = (
      _DATE_TIME +
      pyparsing.Word(pyparsing.alphas).setResultsName('level') +
      _PROCESS_IDENTIFIER +
      # TODO: consider stripping thread identifier/cleaning up thread name?
      _THREAD.setResultsName('thread') +
      pyparsing.Word(pyparsing.printables).setResultsName('source_code') +
      pyparsing.SkipTo(_GDS_ENTRY_END).setResultsName('message') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [('logline', _GDS_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def _BuildDateTime(self, time_elements_structure):
    """Builds time elements from a PostgreSQL log time stamp.

    Args:
      time_elements_structure (pyparsing.ParseResults): structure of tokens
          derived from a PostgreSQL log time stamp.

    Returns:
      dfdatetime.TimeElements: date and time extracted from the structure or
          None if the structure does not represent a valid string.
    """
    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exist.
    try:
      (year, month, day_of_month, hours, minutes, seconds, milliseconds,
       time_zone_group) = time_elements_structure

      time_zone_sign, time_zone_hours, time_zone_minutes = time_zone_group

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
      if time_zone_sign == '-':
        time_zone_offset *= -1

      return dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=time_zone_offset)

    except (TypeError, ValueError):
      return None

  def _ParseRecordLogline(self, parser_mediator, structure):
    """Parses a logline record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    # Replace newlines with spaces in structure.message to preserve output.
    message = self._GetValueFromStructure(structure, 'message')
    if message:
      message = message.replace('\n', ' ').strip(' ')

    event_data = GoogleDriveSyncLogEventData()
    event_data.added_time = self._BuildDateTime(time_elements_structure)
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
    event_data.thread = self._GetValueFromStructure(structure, 'thread')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')
    event_data.message = message

    parser_mediator.ProduceEventData(event_data)

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
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    self._ParseRecordLogline(parser_mediator, structure)

  def VerifyStructure(self, parser_mediator, lines):
    """Verify that this file is a Google Drive Sync log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._GDS_LINE.parseString(lines)
    except pyparsing.ParseException as exception:
      logger.debug('Not a Google Drive Sync log file: {0!s}'.format(exception))
      return False

    date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    date_time = self._BuildDateTime(time_elements_structure)

    if not date_time:
      return False

    return True


manager.ParsersManager.RegisterParser(GoogleDriveSyncLogParser)
