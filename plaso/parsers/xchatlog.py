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
"""This file contains XChat log file parser in plaso.

   Information updated 24 July 2013.

   The parser applies to XChat log files. Despite their apparent
   simplicity it's not straightforward to manage every possible case.
   XChat tool allows users to specify how timestamp will be
   encoded (using the strftime function), by letting them to specify
   additional separators. This parser will accept only the simplest
   default English form of an XChat log file, as the following:

   **** BEGIN LOGGING AT Mon Dec 31 21:11:55 2001

   dec 31 21:11:55 --> You are now talking on #gugle
   dec 31 21:11:55 --- Topic for #gugle is plaso, nobody knows what it means
   dec 31 21:11:55	Topic for #gugle set by Kristinn
   dec 31 21:11:55 --- Joachim gives voice to fpi
   dec 31 21:11:55 *   XChat here
   dec 31 21:11:58 <fpi> ola plas-ing guys!
   dec 31 21:12:00 <Kristinn> ftw!

   It could be managed the missing month/day case too, by extracting
   the month/day information from the header. But the parser logic
   would become intricated, since it would need to manage day transition,
   chat lines crossing the midnight. From there derives the last day of
   the year bug, since the parser will not manage that transition.

   Moreover the strftime is locale-dependant, so month names, footer and
   headers can change, even inside the same log file. Being said that, the
   following will be the main logic used to parse the log files (note that
   the first header *must be* '**** BEGIN ...' otherwise file will be skipped).

   1) Check for '****'
   1.1) If 'BEGIN LOGGING AT' (English)
    1.1.1) Extract the YEAR
    1.1.2) Generate new event start logging
    1.1.3) set parsing = True
   1.2) If 'END LOGGING'
    1.2.1) If parsing, set parsing=False
    1.2.2) If not parsing, log debug
    1.2.3) Geneate new event end logging
   1.3) If not BEGIN|END we are facing a different language
        and we don't now which language!
        If parsing is True, set parsing=False and log debug
   2) Not '****' so we are parsing a line
   2.1) If parsing = True, try to parse line and generate event
   2.2) If parsing = False, skip until next good header is found

   References
   http://xchat.org
"""

import logging
import pyparsing
import pytz

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import text_parser
from plaso.lib import timelib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatLogEvent(event.TimestampEvent):
  """Convenience class for a XChat Log line event."""
  DATA_TYPE = 'xchat:log:line'

  def __init__(self, timestamp, text, nickname=None):
    """Initializes the event object.

    Args:
      timestamp: Microseconds since Epoch in UTC.
      text: The text sent by nickname or other text (server, messages, etc.).
    """
    super(XChatLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.text = text
    if nickname:
      self.nickname = nickname


class XChatLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse XChat log files."""

  NAME = 'xchatlog'

  ENCODING = 'UTF-8'

  # Common (header/footer/body) pyparsing structures.
  # TODO: Only English ASCII timestamp supported ATM, add support for others.
  IGNORE_STRING = pyparsing.Word(pyparsing.printables).suppress()
  LOG_ACTION = pyparsing.Word(
      pyparsing.printables, min=3, max=5).setResultsName('log_action')
  MONTH_NAME = pyparsing.Word(
      pyparsing.printables, exact=3).setResultsName('month_name')
  DAY = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast).setResultsName('day')
  TIME = text_parser.PyparsingConstants.TIME.setResultsName('time')
  YEAR = text_parser.PyparsingConstants.YEAR.setResultsName('year')
  NICKNAME = pyparsing.QuotedString(
      u'<', endQuoteChar=u'>').setResultsName('nickname')
  TEXT = pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text')

  # Header/footer pyparsing structures.
  # Sample: "**** BEGIN LOGGING AT Mon Dec 31 21:11:55 2011".
  # Note that "BEGIN LOGGING" text is localized (default, English) and can be
  # different if XChat locale is different.
  HEADER_SIGNATURE = pyparsing.Keyword(u'****')
  HEADER = (HEADER_SIGNATURE.suppress() + LOG_ACTION +
      pyparsing.Keyword(u'LOGGING AT').suppress() + IGNORE_STRING +
      MONTH_NAME + DAY + TIME + YEAR)

  # Body (nickname, text and/or service messages) pyparsing structures.
  # Sample: "dec 31 21:11:58 <fpi> ola plas-ing guys!".
  LOG_LINE = MONTH_NAME + DAY + TIME + pyparsing.Optional(NICKNAME) + TEXT

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', LOG_LINE),
      ('header', HEADER),
      ('header_signature', HEADER_SIGNATURE),
  ]

  def __init__(self, pre_obj, config=None):
    """XChatLog parser object constructor."""
    super(XChatLogParser, self).__init__(pre_obj, config)
    self.offset = 0
    self.local_zone = getattr(pre_obj, 'zone', pytz.utc)
    self.xchat_year = 0

  def VerifyStructure(self, line):
    """Verify that this file is a XChat log file."""
    try:
      parse_result = self.HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Unable to parse, not a valid XChat log file header')
      return False
    timestamp = self._GetTimestamp(parse_result)
    if not timestamp:
      logging.debug(u'Wrong XChat timestamp: {}'.format(parse_result))
      return False
    # Unset the xchat_year since we are only verifying structure.
    # The value gets set in _GetTimestamp during the actual parsing.
    self.xchat_year = 0
    return True

  def ParseRecord(self, key, structure):
    """Parse each record structure and return an EventObject if applicable."""
    if key == 'logline':
      if not self.xchat_year:
        logging.debug(u'XChatLogParser, missing year information.')
        return
      timestamp = self._GetTimestamp(structure, self.xchat_year)
      if not timestamp:
        logging.debug(u'XChatLogParser, cannot get timestamp from line.')
        return
      # The text string contains multiple unnecessary whitespaces that need to
      # be removed, thus the split and re-join.
      return XChatLogEvent(
          timestamp, u' '.join(structure.text.split()), structure.nickname)
    elif key == 'header':
      timestamp = self._GetTimestamp(structure)
      if not timestamp:
        logging.warning(u'XChatLogParser, cannot get timestamp from header.')
        return
      if structure.log_action == u'BEGIN':
        return XChatLogEvent(timestamp, u'XChat start logging')
      elif structure.log_action == u'END':
        # End logging, unset year.
        self.xchat_year = 0
        return XChatLogEvent(timestamp, u'XChat end logging')
      else:
        logging.warning(u'Unknown log action: {:s}.'.format(
            structure.log_action))
    elif key == 'header_signature':
      # If this key is matched (after others keys failed) we got a different
      # localized header and we should stop parsing until a new good header
      # is found. Stop parsing is done setting xchat_year to 0.
      # Note that the code assumes that LINE_STRUCTURES will be used in the
      # exact order as defined!
      logging.warning(u'Unknown locale header.')
      self.xchat_year = 0
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {}'.format(key))

  def _GetTimestamp(self, parse_result, year=0):
    """Gets a timestamp from the pyparsing ParseResults.

    Args:
      parse_result: The pyparsing ParseResults object.
      year: The current XChat year information, default to 0.

    Returns:
      timestamp: A plaso timelib timestamp event or 0.
    """
    timestamp = 0
    month = timelib.MONTH_DICT.get(parse_result.month_name.lower(), None)
    if not month:
      logging.debug(
          u'XChatLog unmanaged  month name [{}]'.format(
          parse_result.month_name))
      return 0
    hour, minute, second = parse_result.time
    if not year:
      # This condition could happen when parsing the header line: if unable
      # to get a valid year, returns a '0' timestamp, thus preventing any
      # log line parsing (since xchat_year is unset to '0') until a new good
      # (it means supported) header with a valid year information is found.
      # TODO: reconsider this behaviour.
      year = parse_result.get('year', 0)

      if not year:
        return year

      self.xchat_year = year

    day = parse_result.get('day', 0)
    timestamp = timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second, timezone=self.local_zone)
    return timestamp
