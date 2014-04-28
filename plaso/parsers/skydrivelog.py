#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains SkyDrive log file parser in plaso."""

import logging
import pyparsing

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import text_parser
from plaso.lib import timelib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogEvent(event.TimestampEvent):
  """Convenience class for a SkyDrive log line event."""
  DATA_TYPE = 'skydrive:log:line'

  def __init__(self, timestamp, offset, source_code, log_level, text):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value, epoch.
      source_code: Details of the source code file generating the event.
      log_level: The log level used for the event.
      text: The log message.
    """
    super(SkyDriveLogEvent, self).__init__(timestamp,
      eventdata.EventTimestamp.ADDED_TIME)
    self.offset = offset
    self.source_code = source_code
    self.log_level = log_level
    self.text = text


class SkyDriveLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse SkyDrive log files."""

  NAME = 'skydrive_log'

  ENCODING = 'UTF-8-SIG'

  # Common SDL (SkyDriveLog) pyparsing objects.
  SDL_COLON = pyparsing.Literal(u':')
  SDL_EXCLAMATION = pyparsing.Literal(u'!')

  # Timestamp (08-01-2013 21:22:28.999).
  SDL_TIMESTAMP = (
      text_parser.PyparsingConstants.DATE_REV +
      text_parser.PyparsingConstants.TIME_MSEC).setResultsName('timestamp')

  # SkyDrive source code pyparsing structures.
  SDL_SOURCE_CODE = pyparsing.Combine(
      pyparsing.CharsNotIn(u':') +
      SDL_COLON +
      text_parser.PyparsingConstants.INTEGER +
      SDL_EXCLAMATION +
      pyparsing.Word(pyparsing.printables)).setResultsName('source_code')

  # SkyDriveLogLevel pyparsing structures.
  SDL_LOG_LEVEL = (
      pyparsing.Literal(u'(').suppress() +
      pyparsing.SkipTo(u')').setResultsName('log_level') +
      pyparsing.Literal(u')').suppress())

  # SkyDrive line pyparsing structure.
  SDL_LINE = (
      SDL_TIMESTAMP + SDL_SOURCE_CODE + SDL_LOG_LEVEL +
      SDL_COLON + pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  # Sometimes the timestamped log line is followed by an empy line,
  # then by a file name plus other data and finally by another empty
  # line. It could happen that a logline is split in two parts.
  # These lines will not be discarded and an event will be generated
  # ad-hoc (see source), based on the last one if available.
  SDL_NO_HEADER_SINGLE_LINE = (
      pyparsing.Optional(pyparsing.Literal(u'->').suppress()) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', SDL_LINE),
      ('no_header_single_line', SDL_NO_HEADER_SINGLE_LINE),
  ]

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(SkyDriveLogParser, self).__init__(pre_obj, config)
    self.offset = 0
    self.last_event = None

  def VerifyStructure(self, line):
    """Verify that this file is a SkyDrive log file."""
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
      logging.debug(u'Not a SkyDrive log file, invalid timestamp{}'.format(
          parsed_structure.timestamp))
      return False
    return True

  def ParseRecord(self, key, structure):
    """Parse each record structure and return an EventObject if applicable."""
    if key == 'logline':
      return self._ParseLogline(structure)
    elif key == 'no_header_single_line':
      return self._ParseNoHeaderSingleLine(structure)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def _ParseLogline(self, structure):
    """Parse a logline and store appropriate attributes."""
    timestamp = self._GetTimestamp(structure.timestamp)
    if not timestamp:
      logging.debug(u'Invalid timestamp {}'.format(structure.timestamp))
      return
    evt = SkyDriveLogEvent(timestamp, self.offset, structure.source_code,
        structure.log_level, structure.text)
    self.last_event = evt
    return evt

  def _ParseNoHeaderSingleLine(self, structure):
    """Parse an isolated line and store appropriate attributes."""
    if not self.last_event:
      logging.debug(u'SkyDrive, found isolated line with no previous events')
      return
    evt = SkyDriveLogEvent(self.last_event.timestamp, self.last_event.offset,
        None, None, structure.text)
    # TODO think to a possible refactoring for the non-header lines.
    self.last_event = None
    return evt

  def _GetTimestamp(self, timestamp_pypr):
    """Gets a timestamp from a pyparsing ParseResults timestamp.

    This is a timestamp_string as returned by using
    text_parser.PyparsingConstants structures:
    [[8, 1, 2013], [21, 22, 28], 999]

    Args:
      timestamp_string: The pyparsing ParseResults object

    Returns:
      timestamp: A plaso timelib timestamp event or 0.
    """
    timestamp = 0
    try:
      month, day, year = timestamp_pypr[0]
      hour, minute, second = timestamp_pypr[1]
      millisecond = timestamp_pypr[2]
      timestamp = timelib.Timestamp.FromTimeParts(
          year, month, day, hour, minute, second,
          microseconds=(millisecond * 1000))
    except ValueError:
      timestamp = 0
    return timestamp
