# -*- coding: utf-8 -*-
"""This file contains SkyDrive log file parser in plaso."""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogEvent(time_events.TimestampEvent):
  """Convenience class for a SkyDrive log line event."""
  DATA_TYPE = u'skydrive:log:line'

  def __init__(self, timestamp, offset, source_code, log_level, text):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an interger containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      source_code: Details of the source code file generating the event.
      log_level: The log level used for the event.
      text: The log message.
    """
    super(SkyDriveLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.log_level = log_level
    self.offset = offset
    self.source_code = source_code
    self.text = text


class SkyDriveLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse SkyDrive log files."""

  NAME = u'skydrive_log'
  DESCRIPTION = u'Parser for OneDrive (or SkyDrive) log files.'

  ENCODING = u'UTF-8-SIG'

  # Common SDL (SkyDriveLog) pyparsing objects.
  SDL_COLON = pyparsing.Literal(u':')
  SDL_EXCLAMATION = pyparsing.Literal(u'!')

  # Timestamp (08-01-2013 21:22:28.999).
  SDL_TIMESTAMP = (
      text_parser.PyparsingConstants.DATE_REV +
      text_parser.PyparsingConstants.TIME_MSEC).setResultsName(u'timestamp')

  # SkyDrive source code pyparsing structures.
  SDL_SOURCE_CODE = pyparsing.Combine(
      pyparsing.CharsNotIn(u':') +
      SDL_COLON +
      text_parser.PyparsingConstants.INTEGER +
      SDL_EXCLAMATION +
      pyparsing.Word(pyparsing.printables)).setResultsName(u'source_code')

  # SkyDriveLogLevel pyparsing structures.
  SDL_LOG_LEVEL = (
      pyparsing.Literal(u'(').suppress() +
      pyparsing.SkipTo(u')').setResultsName(u'log_level') +
      pyparsing.Literal(u')').suppress())

  # SkyDrive line pyparsing structure.
  SDL_LINE = (
      SDL_TIMESTAMP + SDL_SOURCE_CODE + SDL_LOG_LEVEL +
      SDL_COLON + pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  # Sometimes the timestamped log line is followed by an empy line,
  # then by a file name plus other data and finally by another empty
  # line. It could happen that a logline is split in two parts.
  # These lines will not be discarded and an event will be generated
  # ad-hoc (see source), based on the last one if available.
  SDL_NO_HEADER_SINGLE_LINE = (
      pyparsing.Optional(pyparsing.Literal(u'->').suppress()) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', SDL_LINE),
      (u'no_header_single_line', SDL_NO_HEADER_SINGLE_LINE),
  ]

  def __init__(self):
    """Initializes a parser object."""
    super(SkyDriveLogParser, self).__init__()
    self.offset = 0
    self.last_event = None

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a SkyDrive log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    structure = self.SDL_LINE
    parsed_structure = None
    timestamp = None
    try:
      parsed_structure = structure.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a SkyDrive log file')
      return False
    else:
      timestamp = self._GetTimestamp(parsed_structure.timestamp)
    if not timestamp:
      logging.debug(u'Not a SkyDrive log file, invalid timestamp {0:s}'.format(
          parsed_structure.timestamp))
      return False
    return True

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Returns:
      An event object (instance of EventObject) or None.
    """
    if key == u'logline':
      return self._ParseLogline(structure)
    elif key == u'no_header_single_line':
      return self._ParseNoHeaderSingleLine(structure)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def _ParseLogline(self, structure):
    """Parse a logline and store appropriate attributes."""
    timestamp = self._GetTimestamp(structure.timestamp)
    if not timestamp:
      logging.debug(u'Invalid timestamp {0:s}'.format(structure.timestamp))
      return
    event_object = SkyDriveLogEvent(
        timestamp, self.offset, structure.source_code, structure.log_level,
        structure.text)
    self.last_event = event_object
    return event_object

  def _ParseNoHeaderSingleLine(self, structure):
    """Parse an isolated line and store appropriate attributes."""
    if not self.last_event:
      logging.debug(u'SkyDrive, found isolated line with no previous events')
      return
    event_object = SkyDriveLogEvent(
        self.last_event.timestamp, self.last_event.offset, None, None,
        structure.text)
    # TODO think to a possible refactoring for the non-header lines.
    self.last_event = None
    return event_object

  def _GetTimestamp(self, timestamp_pypr):
    """Gets a timestamp from a pyparsing ParseResults timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    [[8, 1, 2013], [21, 22, 28], 999]

    Args:
      timestamp_string: The pyparsing ParseResults object

    Returns:
      The timestamp which is an interger containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.
    """
    month, day, year = timestamp_pypr[0]
    hour, minute, second = timestamp_pypr[1]
    millisecond = timestamp_pypr[2]
    try:
      return timelib.Timestamp.FromTimeParts(
          year, month, day, hour, minute, second,
          microseconds=(millisecond * 1000))
    except ValueError:
      pass

    return 0


manager.ParsersManager.RegisterParser(SkyDriveLogParser)
