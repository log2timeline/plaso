# -*- coding: utf-8 -*-
"""This file contains SkyDrive error log file parser in plaso."""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogErrorEvent(time_events.TimestampEvent):
  """Convenience class for a SkyDrive error log line event."""
  DATA_TYPE = u'skydrive:error:line'

  def __init__(self, timestamp, module, source_code, text, detail):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an interger containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      module: The module name that generated the log line.
      source_code: Logging source file and line number.
      text: The error text message.
      detail: The error details.
    """
    super(SkyDriveLogErrorEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.module = module
    self.source_code = source_code
    self.text = text
    self.detail = detail


class SkyDriveLogErrorParser(text_parser.PyparsingMultiLineTextParser):
  """Parse SkyDrive error log files."""

  NAME = u'skydrive_log_error'
  DESCRIPTION = u'Parser for OneDrive (or SkyDrive) error log files.'

  ENCODING = u'utf-8'

  # Common SDE (SkyDriveError) structures.
  INTEGER_CAST = text_parser.PyParseIntCast
  HYPHEN = text_parser.PyparsingConstants.HYPHEN
  TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS
  TIME_MSEC = text_parser.PyparsingConstants.TIME_MSEC
  MSEC = pyparsing.Word(pyparsing.nums, max=3).setParseAction(INTEGER_CAST)
  COMMA = pyparsing.Literal(u',').suppress()
  DOT = pyparsing.Literal(u'.').suppress()
  IGNORE_FIELD = pyparsing.CharsNotIn(u',').suppress()

  # Header line timestamp (2013-07-25-160323.291).
  SDE_HEADER_TIMESTAMP = pyparsing.Group(
      text_parser.PyparsingConstants.DATE.setResultsName(u'date') + HYPHEN +
      TWO_DIGITS.setResultsName(u'hh') + TWO_DIGITS.setResultsName(u'mm') +
      TWO_DIGITS.setResultsName(u'ss') + DOT +
      MSEC.setResultsName(u'ms')).setResultsName(u'hdr_timestamp')

  # Line timestamp (07-25-13,16:06:31.820).
  SDE_TIMESTAMP = (
      TWO_DIGITS.setResultsName(u'month') + HYPHEN +
      TWO_DIGITS.setResultsName(u'day') + HYPHEN +
      TWO_DIGITS.setResultsName(u'year_short') + COMMA +
      TIME_MSEC.setResultsName(u'time')).setResultsName(u'timestamp')

  # Header start.
  SDE_HEADER_START = (
      pyparsing.Literal(u'######').suppress() +
      pyparsing.Literal(u'Logging started.').setResultsName(u'log_start'))

  # Multiline entry end marker, matched from right to left.
  SDE_ENTRY_END = pyparsing.StringEnd() | SDE_HEADER_START | SDE_TIMESTAMP

  # SkyDriveError line pyparsing structure.
  SDE_LINE = (
      SDE_TIMESTAMP + COMMA +
      IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName(u'module') + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName(u'source_code') + COMMA +
      IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA +
      pyparsing.Optional(pyparsing.CharsNotIn(u',').setResultsName(u'text')) +
      COMMA + pyparsing.SkipTo(SDE_ENTRY_END).setResultsName(u'detail') +
      pyparsing.lineEnd())

  # SkyDriveError header pyparsing structure.
  SDE_HEADER = (
      SDE_HEADER_START +
      pyparsing.Literal(u'Version=').setResultsName(u'ver_str') +
      pyparsing.Word(pyparsing.nums + u'.').setResultsName(u'ver_num') +
      pyparsing.Literal(u'StartSystemTime:').suppress() +
      SDE_HEADER_TIMESTAMP +
      pyparsing.Literal(u'StartLocalTime:').setResultsName(u'lt_str') +
      pyparsing.SkipTo(pyparsing.lineEnd()).setResultsName(u'details') +
      pyparsing.lineEnd())

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', SDE_LINE),
      (u'header', SDE_HEADER)
  ]

  def __init__(self):
    """Initializes a parser object."""
    super(SkyDriveLogErrorParser, self).__init__()
    self.use_local_zone = False

  def _GetTimestampFromHeader(self, structure):
    """Gets a timestamp from the structure.

    The following is an example of the timestamp structure expected
    [[2013, 7, 25], 16, 3, 23, 291]

    Args:
      structure: The parsed structure, which should be a timestamp.

    Returns:
      timestamp: A plaso timelib timestamp event or 0.
    """
    year, month, day = structure.date
    hour = structure.get(u'hh', 0)
    minute = structure.get(u'mm', 0)
    second = structure.get(u'ss', 0)
    microsecond = structure.get(u'ms', 0) * 1000

    return timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second, microseconds=microsecond)

  def _GetTimestampFromLine(self, structure):
    """Gets a timestamp from string from the structure

    The following is an example of the timestamp structure expected
    [7, 25, 13, [16, 3, 24], 649]

    Args:
      structure: The parsed structure.

    Returns:
      timestamp: A plaso timelib timestamp event or 0.
    """
    hour, minute, second = structure.time[0]
    microsecond = structure.time[1] * 1000
    # TODO: Verify if timestamps are locale dependent.
    year = structure.get(u'year_short', 0)
    month = structure.get(u'month', 0)
    day = structure.get(u'day', 0)
    if year < 0 or not month or not day:
      return 0

    year += 2000

    return timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second, microseconds=microsecond)

  def _ParseHeader(self, parser_mediator, structure):
    """Parse header lines and store appropriate attributes.

    [u'Logging started.', u'Version=', u'17.0.2011.0627',
    [2013, 7, 25], 16, 3, 23, 291, u'StartLocalTime', u'<details>']

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    timestamp = self._GetTimestampFromHeader(structure.hdr_timestamp)
    if not timestamp:
      logging.debug(
          u'SkyDriveLogError invalid timestamp {0:d}'.format(
              structure.hdr_timestamp))
      return

    text = u'{0:s} {1:s} {2:s}'.format(
        structure.log_start, structure.ver_str, structure.ver_num)
    detail = u'{0:s} {1:s}'.format(structure.lt_str, structure.details)
    event_object = SkyDriveLogErrorEvent(
        timestamp, None, None, text, detail)
    parser_mediator.ProduceEvent(event_object)

  def _ParseLine(self, parser_mediator, structure):
    """Parse a logline and store appropriate attributes.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    timestamp = self._GetTimestampFromLine(structure.timestamp)
    if not timestamp:
      logging.debug(u'SkyDriveLogError invalid timestamp {0:s}'.format(
          structure.timestamp))
      return

    # Replace newlines with spaces in structure.detail to preserve output.
    detail = structure.detail.replace(u'\n', u' ')
    event_object = SkyDriveLogErrorEvent(
        timestamp, structure.module, structure.source_code, structure.text,
        detail)
    parser_mediator.ProduceEvent(event_object)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key == u'logline':
      self._ParseLine(parser_mediator, structure)
    elif key == u'header':
      self._ParseHeader(parser_mediator, structure)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a SkyDrive Error log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      parsed_structure = self.SDE_HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a SkyDrive Error log file')
      return False
    timestamp = self._GetTimestampFromHeader(parsed_structure.hdr_timestamp)
    if not timestamp:
      logging.debug(
          u'Not a SkyDrive Error log file, invalid timestamp {0:s}'.format(
              parsed_structure.timestamp))
      return False
    return True


manager.ParsersManager.RegisterParser(SkyDriveLogErrorParser)
