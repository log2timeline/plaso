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
  """Convenience class for a SkyDrive log line event.

  Attributes:
    detail: The log line details.
    log_level: Optional, the SkyDrive log level short name.
    module: Optional, the module name that generated the log line.
    source_code: Optional, logging source file and line number.
  """
  DATA_TYPE = u'skydrive:log:line'

  def __init__(
      self, timestamp, detail, module=None, source_code=None, log_level=None):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      detail: The log line details.
      module: Optional, the module name that generated the log line.
      source_code: Optional, logging source file and line number.
      log_level: Optional, the SkyDrive log level short name.
    """
    super(SkyDriveLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.detail = detail
    self.log_level = log_level
    self.module = module
    self.source_code = source_code


class SkyDriveOldLogEvent(time_events.TimestampEvent):
  """Convenience class for a SkyDrive old log line event.

  Attributes:
    log_level: The log level used for the event.
    source_code: Details of the source code file generating the event.
    text: The log message.
  """
  DATA_TYPE = u'skydrive:log:old:line'

  def __init__(self, timestamp, offset, source_code, log_level, text):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      source_code: Details of the source code file generating the event.
      log_level: The log level used for the event.
      text: The log message.
    """
    super(SkyDriveOldLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.log_level = log_level
    self.offset = offset
    self.source_code = source_code
    self.text = text


class SkyDriveLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses SkyDrive log files."""

  NAME = u'skydrive_log'
  DESCRIPTION = u'Parser for OneDrive (or SkyDrive) log files.'

  _ENCODING = u'utf-8'

  # Common SDF (SkyDrive Format) structures.
  INTEGER_CAST = text_parser.PyParseIntCast
  HYPHEN = text_parser.PyparsingConstants.HYPHEN
  TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS
  TIME_MSEC = text_parser.PyparsingConstants.TIME_MSEC
  MSEC = pyparsing.Word(pyparsing.nums, max=3).setParseAction(INTEGER_CAST)
  COMMA = pyparsing.Literal(u',').suppress()
  DOT = pyparsing.Literal(u'.').suppress()
  IGNORE_FIELD = pyparsing.CharsNotIn(u',').suppress()

  # Header line timestamp (2013-07-25-160323.291): the timestamp format is
  # YYYY-MM-DD-hhmmss.msec.
  SDF_HEADER_TIMESTAMP = pyparsing.Group(
      text_parser.PyparsingConstants.DATE.setResultsName(u'date') + HYPHEN +
      TWO_DIGITS.setResultsName(u'hh') + TWO_DIGITS.setResultsName(u'mm') +
      TWO_DIGITS.setResultsName(u'ss') + DOT +
      MSEC.setResultsName(u'ms')).setResultsName(u'hdr_timestamp')

  # Line timestamp (07-25-13,16:06:31.820): the timestamp format is
  # MM-DD-YY,hh:mm:ss.msec.
  SDF_TIMESTAMP = (
      TWO_DIGITS.setResultsName(u'month') + HYPHEN +
      TWO_DIGITS.setResultsName(u'day') + HYPHEN +
      TWO_DIGITS.setResultsName(u'year_short') + COMMA +
      TIME_MSEC.setResultsName(u'time')).setResultsName(u'timestamp')

  # Header start.
  SDF_HEADER_START = (
      pyparsing.Literal(u'######').suppress() +
      pyparsing.Literal(u'Logging started.').setResultsName(u'log_start'))

  # Multiline entry end marker, matched from right to left.
  SDF_ENTRY_END = pyparsing.StringEnd() | SDF_HEADER_START | SDF_TIMESTAMP

  # SkyDrive line pyparsing structure.
  SDF_LINE = (
      SDF_TIMESTAMP + COMMA +
      IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName(u'module') + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName(u'source_code') + COMMA +
      IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName(u'log_level') + COMMA +
      pyparsing.SkipTo(SDF_ENTRY_END).setResultsName(u'detail') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  # SkyDrive header pyparsing structure.
  SDF_HEADER = (
      SDF_HEADER_START +
      pyparsing.Literal(u'Version=').setResultsName(u'version_string') +
      pyparsing.Word(pyparsing.nums + u'.').setResultsName(u'version_number') +
      pyparsing.Literal(u'StartSystemTime:').suppress() +
      SDF_HEADER_TIMESTAMP +
      pyparsing.Literal(u'StartLocalTime:').setResultsName(
          u'local_time_string') +
      pyparsing.SkipTo(pyparsing.lineEnd()).setResultsName(u'details') +
      pyparsing.lineEnd())

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', SDF_LINE),
      (u'header', SDF_HEADER)
  ]

  def __init__(self):
    """Initializes a parser object."""
    super(SkyDriveLogParser, self).__init__()
    self.use_local_zone = False

  def _GetTimestampFromHeader(self, structure):
    """Gets a timestamp from the structure.

    The following is an example of the timestamp structure expected
    [[2013, 7, 25], 16, 3, 23, 291]: DATE (year, month, day)  is the
    first list element, than hours, minutes, seconds and milliseconds follow.

    Args:
      structure: The parsed structure, which should be a timestamp.

    Returns:
      timestamp: An integer containing the timestamp or 0 on error.
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
    [7, 25, 13, [16, 3, 24], 649]: month, day, year, a list with three
    element (hours, minutes, seconds) and finally milliseconds.

    Args:
      structure: The parsed structure.

    Returns:
      timestamp: An integer containing the timestamp or 0 on error.
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

  def _ParseHeader(self, structure):
    """Parse header lines and store appropriate attributes.

    [u'Logging started.', u'Version=', u'17.0.2011.0627',
    [2013, 7, 25], 16, 3, 23, 291, u'StartLocalTime', u'<details>']

    Args:
      structure: A pyparsing.ParseResults object from an header line in the
                 log file.

    Returns:
      An event object (instance of SkyDriveLogEvent) or None on error.
    """
    timestamp = self._GetTimestampFromHeader(structure.hdr_timestamp)
    if not timestamp:
      logging.debug(
          u'SkyDriveLog invalid timestamp {0:d}'.format(
              structure.hdr_timestamp))
      return
    detail = u'{0:s} {1:s} {2:s} {3:s} {4:s}'.format(
        structure.log_start, structure.version_string,
        structure.version_number, structure.local_time_string,
        structure.details)
    return SkyDriveLogEvent(timestamp, detail)

  def _ParseLine(self, structure):
    """Parse a logline and store appropriate attributes.

    Args:
      structure: A pyparsing.ParseResults object from a line in the log file.

    Returns:
      An event object (instance of SkyDriveLogEvent) or None.
    """
    timestamp = self._GetTimestampFromLine(structure.timestamp)
    if not timestamp:
      logging.debug(u'SkyDriveLog invalid timestamp {0:s}'.format(
          structure.timestamp))
      return

    # Replace newlines with spaces in structure.detail to preserve output.
    detail = structure.detail.replace(u'\n', u' ')
    return SkyDriveLogEvent(
        timestamp, detail, module=structure.module,
        source_code=structure.source_code, log_level=structure.log_level)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    event_object = None

    if key == u'logline':
      event_object = self._ParseLine(structure)
    elif key == u'header':
      event_object = self._ParseHeader(structure)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    if event_object:
      parser_mediator.ProduceEvent(event_object)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a SkyDrive log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      parsed_structure = self.SDF_HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a SkyDrive log file')
      return False

    timestamp = self._GetTimestampFromHeader(parsed_structure.hdr_timestamp)
    if not timestamp:
      logging.debug(
          u'Not a SkyDrive log file, invalid timestamp {0:s}'.format(
              parsed_structure.timestamp))
      return False

    return True


class SkyDriveOldLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse SkyDrive old log files."""

  NAME = u'skydrive_log_old'
  DESCRIPTION = u'Parser for OneDrive (or SkyDrive) old log files.'

  _ENCODING = u'UTF-8-SIG'

  # Common SDOL (SkyDriveOldLog) pyparsing objects.
  SDOL_COLON = pyparsing.Literal(u':')
  SDOL_EXCLAMATION = pyparsing.Literal(u'!')

  # Timestamp (08-01-2013 21:22:28.999).
  SDOL_TIMESTAMP = (
      text_parser.PyparsingConstants.DATE_REV +
      text_parser.PyparsingConstants.TIME_MSEC).setResultsName(
          u'sdol_timestamp')

  # SkyDrive source code pyparsing structures.
  SDOL_SOURCE_CODE = pyparsing.Combine(
      pyparsing.CharsNotIn(u':') +
      SDOL_COLON +
      text_parser.PyparsingConstants.INTEGER +
      SDOL_EXCLAMATION +
      pyparsing.Word(pyparsing.printables)).setResultsName(u'source_code')

  # SkyDriveOldLogLevel pyparsing structures.
  SDOL_LOG_LEVEL = (
      pyparsing.Literal(u'(').suppress() +
      pyparsing.SkipTo(u')').setResultsName(u'log_level') +
      pyparsing.Literal(u')').suppress())

  # SkyDrive line pyparsing structure.
  SDOL_LINE = (
      SDOL_TIMESTAMP + SDOL_SOURCE_CODE + SDOL_LOG_LEVEL +
      SDOL_COLON + pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  # Sometimes the timestamped log line is followed by an empy line,
  # then by a file name plus other data and finally by another empty
  # line. It could happen that a logline is split in two parts.
  # These lines will not be discarded and an event will be generated
  # ad-hoc (see source), based on the last one if available.
  SDOL_NO_HEADER_SINGLE_LINE = (
      pyparsing.Optional(pyparsing.Literal(u'->').suppress()) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', SDOL_LINE),
      (u'no_header_single_line', SDOL_NO_HEADER_SINGLE_LINE),
  ]

  def __init__(self):
    """Initializes a parser object."""
    super(SkyDriveOldLogParser, self).__init__()
    self.last_event_object = None
    self.offset = 0

  def _GetTimestamp(self, sdol_timestamp):
    """Gets a timestamp from a pyparsing ParseResults SkyDriveOld timestamp.

    This is a sdol_timestamp object as returned by using
    text_parser.PyparsingConstants structures:
    [[month, day, year], [hours, minutes, seconds], milliseconds], for example
    [[8, 1, 2013], [21, 22, 28], 999].

    Args:
      sdol_timestamp: The pyparsing ParseResults object.

    Returns:
      timestamp: A plaso timelib timestamp or None.
    """
    try:
      month, day, year = sdol_timestamp[0]
      hour, minute, second = sdol_timestamp[1]
      millisecond = sdol_timestamp[2]
      return timelib.Timestamp.FromTimeParts(
          year, month, day, hour, minute, second,
          microseconds=millisecond * 1000)
    except ValueError:
      pass

  def _ParseLogline(self, structure):
    """Parse a logline and store appropriate attributes.

    Args:
      structure: A pyparsing.ParseResults object from a line in the log file.

    Returns:
      An event object (instance of SkyDriveOldLogEvent) or None.
    """
    timestamp = self._GetTimestamp(structure.sdol_timestamp)
    if not timestamp:
      logging.debug(u'Invalid timestamp {0:s}'.format(
          structure.sdol_timestamp))
      return

    event_object = SkyDriveOldLogEvent(
        timestamp, self.offset, structure.source_code, structure.log_level,
        structure.text)
    self.last_event_object = event_object
    return event_object

  def _ParseNoHeaderSingleLine(self, structure):
    """Parse an isolated header line and store appropriate attributes.

    Args:
      structure: A pyparsing.ParseResults object from an header line in the
                 log file.

    Returns:
      An event object (instance of SkyDriveOldLogEvent) or None.
    """
    if not self.last_event_object:
      logging.debug(u'SkyDrive, found isolated line with no previous events')
      return

    event_object = SkyDriveOldLogEvent(
        self.last_event_object.timestamp, self.last_event_object.offset, None,
        None, structure.text)
    # TODO think to a possible refactoring for the non-header lines.
    self.last_event_object = None
    return event_object

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

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a SkyDrive old log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      parsed_structure = self.SDOL_LINE.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a SkyDrive old log file')
      return False

    timestamp = self._GetTimestamp(parsed_structure.sdol_timestamp)
    if not timestamp:
      logging.debug(
          u'Not a SkyDrive old log file, invalid timestamp {0:s}'.format(
              parsed_structure.sdol_timestamp))
      return False

    return True


manager.ParsersManager.RegisterParsers([
    SkyDriveLogParser, SkyDriveOldLogParser])
