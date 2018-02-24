# -*- coding: utf-8 -*-
"""Parser for Google Drive Sync log files."""

from __future__ import unicode_literals

import logging

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class GoogleDriveSyncLogEventData(events.EventData):
  """Google Drive Sync log event data.

  Attributes:
    log_level (str): logging level of event such as "DEBUG", "WARN", "INFO",
        "ERROR".
    message (str): log message.
    pid (int): process identifier of process which logged event.
    source_code (str): filename:line_number of source file which logged event.
    thread (str): colon-separated thread identifier in the form "ID:name"
        which logged event.
    time (str): date and time of the log entry event with timezone offset.
  """

  DATA_TYPE = 'gdrive_sync:log:line'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSyncLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.time = None
    self.log_level = None
    self.pid = None
    self.thread = None
    self.source_code = None
    self.message = None


class GoogleDriveSyncLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from Google Drive Sync log files."""

  NAME = 'gdrive_synclog'

  DESCRIPTION = 'Parser for Google Drive Sync log files.'

  _ENCODING = 'utf-8'

  # Increase the buffer size, as log messages are often many lines of Python
  # object dumps or similar. The default is too small for this and results in
  # premature end of string matching on multi-line log entries.
  BUFFER_SIZE = 16384

  _HYPHEN = text_parser.PyparsingConstants.HYPHEN

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  _GDS_DATE_TIME = (
      _FOUR_DIGITS.setResultsName('year') + _HYPHEN +
      _TWO_DIGITS.setResultsName('month') + _HYPHEN +
      _TWO_DIGITS.setResultsName('day') +
      text_parser.PyparsingConstants.TIME_MSEC_ELEMENTS +
      pyparsing.Word(pyparsing.printables).setResultsName('time_zone_offset')
  ).setResultsName('date_time')

  # Multiline entry end marker, matched from right to left.
  _GDS_ENTRY_END = pyparsing.StringEnd() | _GDS_DATE_TIME

  _GDS_LINE = (
      _GDS_DATE_TIME +
      pyparsing.Word(pyparsing.alphas).setResultsName('log_level') +
      # TODO: strip pid= out, cast to integers?
      pyparsing.Word(pyparsing.printables).setResultsName('pid') +
      # TODO: consider stripping thread identifier/cleaning up thread name?
      pyparsing.Word(pyparsing.printables).setResultsName('thread') +
      pyparsing.Word(pyparsing.printables).setResultsName('source_code') +
      pyparsing.SkipTo(_GDS_ENTRY_END).setResultsName('message') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [
      ('logline', _GDS_LINE),
  ]

  def _GetISO8601String(self, structure):
    """Retrieves an ISO 8601 date time string from the structure.

    The date and time values in Google Drive Sync log files are formatted as:
    "2018-01-24 18:25:08,454 -0800".

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from a
          line of a text file.

    Returns:
      str: ISO 8601 date time string.

    Raises:
      ValueError: if the structure cannot be converted into a date time string.
    """
    time_zone_offset = structure.time_zone_offset

    try:
      time_zone_offset_hours = int(time_zone_offset[1:3], 10)
      time_zone_offset_minutes = int(time_zone_offset[3:5], 10)
    except (IndexError, TypeError, ValueError) as exception:
      raise ValueError(
          'unable to parse time zone offset with error: {0!s}.'.format(
              exception))

    try:
      iso8601 = (
          '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.{6:03d}'
          '{7:s}{8:02d}:{9:02d}').format(
              structure.year, structure.month, structure.day,
              structure.hours, structure.minutes, structure.seconds,
              structure.microseconds, time_zone_offset[0],
              time_zone_offset_hours, time_zone_offset_minutes)
    except ValueError as exception:
      raise ValueError(
          'unable to format date time string with error: {0!s}.'.format(
              exception))

    return iso8601

  def _ParseRecordLogline(self, parser_mediator, structure):
    """Parses a logline record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()

    try:
      datetime_iso8601 = self._GetISO8601String(structure.date_time)
      date_time.CopyFromStringISO8601(datetime_iso8601)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          'invalid date time value: {0!s}'.format(structure.date_time))
      return

    event_data = GoogleDriveSyncLogEventData()
    event_data.log_level = structure.log_level
    event_data.pid = structure.pid
    event_data.thread = structure.thread
    event_data.source_code = structure.source_code
    # Replace newlines with spaces in structure.message to preserve output.
    event_data.message = structure.message.replace('\n', ' ')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)

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
      logging.debug('Not a Google Drive Sync log file: {0!s}'.format(exception))
      return False

    date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()

    try:
      datetime_iso8601 = self._GetISO8601String(structure.date_time)
      date_time.CopyFromStringISO8601(datetime_iso8601)
    except ValueError:
      logging.debug(
          'Not a Google Drive Sync log file, invalid date/time: {0!s}'.format(
              structure.date_time))
      return False

    return True


manager.ParsersManager.RegisterParser(GoogleDriveSyncLogParser)
