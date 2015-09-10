# -*- coding: utf-8 -*-
# There's a backslash in the module docstring, so as not to confuse Sphinx.
# pylint: disable=anomalous-backslash-in-string
"""This file contains XChat log file parser in plaso.

Information updated 24 July 2013.

The parser applies to XChat log files. Despite their apparent
simplicity it's not straightforward to manage every possible case.
XChat tool allows users to specify how timestamp will be
encoded (using the strftime function), by letting them to specify
additional separators. This parser will accept only the simplest
default English form of an XChat log file, as the following::

  **** BEGIN LOGGING AT Mon Dec 31 21:11:55 2001
  dec 31 21:11:55 --> You are now talking on #gugle
  dec 31 21:11:55 --- Topic for #gugle is plaso, nobody knows what it means
  dec 31 21:11:55 Topic for #gugle set by Kristinn
  dec 31 21:11:55 --- Joachim gives voice to fpi
  dec 31 21:11:55 *   XChat here
  dec 31 21:11:58 <fpi> ola plas-ing guys!
  dec 31 21:12:00 <Kristinn> ftw!

It could be managed the missing month/day case too, by extracting
the month/day information from the header. But the parser logic
would become intricate, since it would need to manage day transition,
chat lines crossing the midnight. From there derives the last day of
the year bug, since the parser will not manage that transition.

Moreover the strftime is locale-dependant, so month names, footer and
headers can change, even inside the same log file. Being said that, the
following will be the main logic used to parse the log files (note that
the first header *must be* '\*\*\*\* BEGIN ...' otherwise file will be skipped).

1) Check for '\*\*\*\*'
1.1) If 'BEGIN LOGGING AT' (English)
1.1.1) Extract the YEAR
1.1.2) Generate new event start logging
1.1.3) set parsing = True
1.2) If 'END LOGGING'
1.2.1) If parsing, set parsing=False
1.2.2) If not parsing, log debug
1.2.3) Generate new event end logging
1.3) If not BEGIN|END we are facing a different language
and we don't now which language!
If parsing is True, set parsing=False and log debug
2) Not '\*\*\*\*' so we are parsing a line
2.1) If parsing = True, try to parse line and generate event
2.2) If parsing = False, skip until next good header is found

References
http://xchat.org
"""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatLogEvent(time_events.TimestampEvent):
  """Convenience class for a XChat Log line event."""
  DATA_TYPE = u'xchat:log:line'

  def __init__(self, timestamp, text, nickname=None):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      text: The text sent by nickname or other text (server, messages, etc.).
      nickname: optional string containing the XChat nickname.
    """
    super(XChatLogEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.text = text
    if nickname:
      self.nickname = nickname


class XChatLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse XChat log files."""

  NAME = u'xchatlog'
  DESCRIPTION = u'Parser for XChat log files.'

  ENCODING = u'UTF-8'

  # Common (header/footer/body) pyparsing structures.
  # TODO: Only English ASCII timestamp supported ATM, add support for others.
  IGNORE_STRING = pyparsing.Word(pyparsing.printables).suppress()
  LOG_ACTION = pyparsing.Word(
      pyparsing.printables, min=3, max=5).setResultsName(u'log_action')
  MONTH_NAME = pyparsing.Word(
      pyparsing.printables, exact=3).setResultsName(u'month_name')
  DAY = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast).setResultsName(u'day')
  TIME = text_parser.PyparsingConstants.TIME.setResultsName(u'time')
  YEAR = text_parser.PyparsingConstants.YEAR.setResultsName(u'year')
  NICKNAME = pyparsing.QuotedString(
      u'<', endQuoteChar=u'>').setResultsName(u'nickname')
  TEXT = pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text')

  # Header/footer pyparsing structures.
  # Sample: "**** BEGIN LOGGING AT Mon Dec 31 21:11:55 2011".
  # Note that "BEGIN LOGGING" text is localized (default, English) and can be
  # different if XChat locale is different.
  HEADER_SIGNATURE = pyparsing.Keyword(u'****')
  HEADER = (
      HEADER_SIGNATURE.suppress() + LOG_ACTION +
      pyparsing.Keyword(u'LOGGING AT').suppress() + IGNORE_STRING +
      MONTH_NAME + DAY + TIME + YEAR)

  # Body (nickname, text and/or service messages) pyparsing structures.
  # Sample: "dec 31 21:11:58 <fpi> ola plas-ing guys!".
  LOG_LINE = MONTH_NAME + DAY + TIME + pyparsing.Optional(NICKNAME) + TEXT

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', LOG_LINE),
      (u'header', HEADER),
      (u'header_signature', HEADER_SIGNATURE),
  ]

  def __init__(self):
    """Initializes a XChatLog parser object."""
    super(XChatLogParser, self).__init__()
    self.offset = 0
    self.xchat_year = 0

  def _GetTimestamp(self, parse_result, timezone, year=0):
    """Determines the timestamp from the pyparsing ParseResults.

    Args:
      parse_result: The pyparsing ParseResults object.
      timezone: The timezone object.
      year: Optional current year. The default is 0.

    Returns:
      A timelib timestamp or 0.
    """
    month = timelib.MONTH_DICT.get(parse_result.month_name.lower(), None)
    if not month:
      logging.debug(u'XChatLog unmanaged month name [{0:s}]'.format(
          parse_result.month_name))
      return 0

    hour, minute, second = parse_result.time
    if not year:
      # This condition could happen when parsing the header line: if unable
      # to get a valid year, returns a '0' timestamp, thus preventing any
      # log line parsing (since xchat_year is unset to '0') until a new good
      # (it means supported) header with a valid year information is found.
      # TODO: reconsider this behaviour.
      year = parse_result.get(u'year', 0)

      if not year:
        return 0

      self.xchat_year = year

    day = parse_result.get(u'day', 0)
    return timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second, timezone=timezone)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a XChat log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      parse_result = self.HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Unable to parse, not a valid XChat log file header')
      return False
    timestamp = self._GetTimestamp(parse_result, parser_mediator.timezone)
    if not timestamp:
      logging.debug(u'Wrong XChat timestamp: {0:s}'.format(parse_result))
      return False
    # Unset the xchat_year since we are only verifying structure.
    # The value gets set in _GetTimestamp during the actual parsing.
    self.xchat_year = 0
    return True

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an event object if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key == u'logline':
      if not self.xchat_year:
        logging.debug(u'XChatLogParser, missing year information.')
        return

      timestamp = self._GetTimestamp(
          structure, parser_mediator.timezone, year=self.xchat_year)
      if not timestamp:
        logging.debug(u'XChatLogParser, cannot get timestamp from line.')
        return

      # The text string contains multiple unnecessary whitespaces that need to
      # be removed, thus the split and re-join.
      event_object = XChatLogEvent(
          timestamp, u' '.join(structure.text.split()), structure.nickname)
      parser_mediator.ProduceEvent(event_object)

    elif key == u'header':
      timestamp = self._GetTimestamp(structure, parser_mediator.timezone)
      if not timestamp:
        logging.warning(u'XChatLogParser, cannot get timestamp from header.')
        return

      if structure.log_action == u'BEGIN':
        event_object = XChatLogEvent(timestamp, u'XChat start logging')
        parser_mediator.ProduceEvent(event_object)

      elif structure.log_action == u'END':
        # End logging, unset year.
        self.xchat_year = 0
        event_object = XChatLogEvent(timestamp, u'XChat end logging')
        parser_mediator.ProduceEvent(event_object)

      else:
        logging.warning(u'Unknown log action: {0:s}.'.format(
            structure.log_action))

    elif key == u'header_signature':
      # If this key is matched (after others keys failed) we got a different
      # localized header and we should stop parsing until a new good header
      # is found. Stop parsing is done setting xchat_year to 0.
      # Note that the code assumes that LINE_STRUCTURES will be used in the
      # exact order as defined!
      logging.warning(u'Unknown locale header.')
      self.xchat_year = 0

    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))


manager.ParsersManager.RegisterParser(XChatLogParser)
