#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains SkyDrive error log file parser in plaso."""

import logging
import pyparsing

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import text_parser
from plaso.lib import timelib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogErrorEvent(event.TimestampEvent):
  """Convenience class for a SkyDrive error log line event."""
  DATA_TYPE = 'skydrive:error:line'

  def __init__(self, timestamp, offset, module, source_code, text, detail):
    """Initializes the event object.

    Args:
      timestamp: Milliseconds since epoch in UTC.
      offset: The offset of the event in the file.
      module: The module name that generated the log line.
      source_code: Logging source file and line number.
      text: The error text message.
      detail: The error details.
    """
    super(SkyDriveLogErrorEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.offset = offset
    self.module = module
    self.source_code = source_code
    self.text = text
    self.detail = detail


class SkyDriveLogErrorParser(text_parser.PyparsingMultiLineTextParser):
  """Parse SkyDrive error log files."""

  NAME = 'skydrive_log_error'

  ENCODING = 'UTF-8'

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
      text_parser.PyparsingConstants.DATE.setResultsName('date') + HYPHEN +
      TWO_DIGITS.setResultsName('hh') + TWO_DIGITS.setResultsName('mm') +
      TWO_DIGITS.setResultsName('ss') + DOT +
      MSEC.setResultsName('ms')).setResultsName('hdr_timestamp')

  # Line timestamp (07-25-13,16:06:31.820).
  SDE_TIMESTAMP = (
      TWO_DIGITS.setResultsName('month') + HYPHEN +
      TWO_DIGITS.setResultsName('day') + HYPHEN +
      TWO_DIGITS.setResultsName('year_short') + COMMA +
      TIME_MSEC.setResultsName('time')).setResultsName('timestamp')

  # Header start.
  SDE_HEADER_START = (pyparsing.Literal(u'######').suppress() +
      pyparsing.Literal(u'Logging started.').setResultsName('log_start'))

  # Multiline entry end marker, matched from right to left.
  SDE_ENTRY_END = pyparsing.StringEnd() | SDE_HEADER_START | SDE_TIMESTAMP

  # SkyDriveError line pyparsing structure.
  SDE_LINE = (
      SDE_TIMESTAMP + COMMA +
      IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName('module') + COMMA +
      pyparsing.CharsNotIn(u',').setResultsName('source_code') + COMMA +
      IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA + IGNORE_FIELD + COMMA +
      pyparsing.Optional(pyparsing.CharsNotIn(u',').setResultsName('text')) +
      COMMA + pyparsing.SkipTo(SDE_ENTRY_END).setResultsName('detail'))

  # SkyDriveError header pyparsing structure.
  SDE_HEADER = (
      SDE_HEADER_START +
      pyparsing.Literal(u'Version=').setResultsName('ver_str') +
      pyparsing.Word(pyparsing.nums + u'.').setResultsName('ver_num') +
      pyparsing.Literal(u'StartSystemTime:').suppress() +
      SDE_HEADER_TIMESTAMP +
      pyparsing.Literal(u'StartLocalTime:').setResultsName('lt_str') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('details'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', SDE_LINE),
      ('header', SDE_HEADER),
  ]


  def __init__(self, pre_obj, config=None):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(SkyDriveLogErrorParser, self).__init__(pre_obj, config)
    self.use_local_zone = False
    self.offset = 0

  def VerifyStructure(self, line):
    """Verify that this file is a SkyDrive Error log file."""
    try:
      parsed_structure = self.SDE_HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a SkyDrive Error log file')
      return False
    timestamp = self._GetTimestampFromHeader(parsed_structure.hdr_timestamp)
    if not timestamp:
      logging.debug(
          u'Not a SkyDrive Error log file, invalid timestamp {}'.format(
          parsed_structure.timestamp))
      return False
    return True

  def ParseRecord(self, key, structure):
    """Parse each record structure and return an EventObject if applicable."""
    if key == 'logline':
      return self._ParseLine(structure)
    elif key == 'header':
      return self._ParseHeader(structure)
    else:
      logging.warning(u'Unable to parse record, unknown structure: %s' % key)

  def _ParseLine(self, structure):
    """Parse a logline and store appropriate attributes."""
    timestamp = self._GetTimestampFromLine(structure.timestamp)
    if not timestamp:
      logging.debug(
          u'SkyDriveLogError invalid timestamp {}'.format(structure.timestamp))
      return
    # Replace newlines with spaces in structure.detail to preserve output.
    return SkyDriveLogErrorEvent(
        timestamp, self.offset, structure.module, structure.source_code,
        structure.text, structure.detail.replace(u'\r\n', u' '))

  def _ParseHeader(self, structure):
    """Parse header lines and store appropriate attributes.

    [u'Logging started.', u'Version=', u'17.0.2011.0627',
    [2013, 7, 25], 16, 3, 23, 291, u'StartLocalTime', u'<details>']

    Args:
      structure: The parsed structure.

    Returns:
      timestamp: The event or none.
    """
    timestamp = self._GetTimestampFromHeader(structure.hdr_timestamp)
    if not timestamp:
      logging.debug(
          u'SkyDriveLogError invalid timestamp {}'.format(
              structure.hdr_timestamp))
      return
    text = u'{} {} {}'.format(
        structure.log_start, structure.ver_str, structure.ver_num)
    detail = u'{} {}'.format(structure.lt_str, structure.details)
    return SkyDriveLogErrorEvent(
        timestamp, self.offset, None, None, text, detail)

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
    try:
      hour = int(structure.hh, 10)
      minute = int(structure.mm, 10)
      second = int(structure.ss, 10)
      microsecond = int(structure.ms, 10) * 1000
    except ValueError:
      logging.warning(u'SkyDriveLogError invalid header timestamp')
      return 0
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second, microsecond)

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
    try:
      year = int(structure.year_short, 10) + 2000
      month = int(structure.month, 10)
      day = int(structure.day, 10)
    except ValueError:
      logging.warning(u'SkyDriveLogError invalid log line timestamp')
      return 0
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second, microsecond) 


