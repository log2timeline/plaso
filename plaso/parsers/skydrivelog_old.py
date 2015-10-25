# -*- coding: utf-8 -*-
"""This file contains SkyDrive old log file parser in plaso."""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveOldLogEvent(time_events.TimestampEvent):
  """Convenience class for a SkyDrive old log line event.

  Attributes:
    source_code: Details of the source code file generating the event.
    log_level: The log level used for the event.
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


manager.ParsersManager.RegisterParser(SkyDriveOldLogParser)
