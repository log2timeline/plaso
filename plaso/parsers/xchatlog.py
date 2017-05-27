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

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatLogEventData(events.EventData):
  """XChat Log event data.

  Attributes:
    nickname (str): nickname.
    text (str): text sent by nickname or other text (server, messages, etc.).
  """

  DATA_TYPE = u'xchat:log:line'

  def __init__(self):
    """Initializes event data."""
    super(XChatLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.nickname = None
    self.text = None


class XChatLogParser(text_parser.PyparsingSingleLineTextParser):
  """Parse XChat log files."""

  NAME = u'xchatlog'
  DESCRIPTION = u'Parser for XChat log files.'

  _ENCODING = u'UTF-8'

  # Common (header/footer/body) pyparsing structures.
  # TODO: Only English ASCII timestamp supported ATM, add support for others.

  _WEEKDAY = pyparsing.Group(
      pyparsing.Keyword(u'Sun') |
      pyparsing.Keyword(u'Mon') |
      pyparsing.Keyword(u'Tue') |
      pyparsing.Keyword(u'Wed') |
      pyparsing.Keyword(u'Thu') |
      pyparsing.Keyword(u'Fri') |
      pyparsing.Keyword(u'Sat'))

  # Header/footer pyparsing structures.
  # Sample: "**** BEGIN LOGGING AT Mon Dec 31 21:11:55 2011".
  # Note that "BEGIN LOGGING" text is localized (default, English) and can be
  # different if XChat locale is different.

  _HEADER_SIGNATURE = pyparsing.Keyword(u'****')
  _HEADER_DATE_TIME = pyparsing.Group(
      _WEEKDAY.setResultsName(u'weekday') +
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS +
      text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName(u'year'))
  _LOG_ACTION = pyparsing.Group(
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables))
  _HEADER = (
      _HEADER_SIGNATURE.suppress() + _LOG_ACTION.setResultsName(u'log_action') +
      _HEADER_DATE_TIME.setResultsName(u'date_time'))

  # Body (nickname, text and/or service messages) pyparsing structures.
  # Sample: "dec 31 21:11:58 <fpi> ola plas-ing guys!".

  _DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName(u'month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(u'day') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)
  _NICKNAME = pyparsing.QuotedString(u'<', endQuoteChar=u'>').setResultsName(
      u'nickname')
  _LOG_LINE = (
      _DATE_TIME.setResultsName(u'date_time') +
      pyparsing.Optional(_NICKNAME) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName(u'text'))

  LINE_STRUCTURES = [
      (u'logline', _LOG_LINE),
      (u'header', _HEADER),
      (u'header_signature', _HEADER_SIGNATURE),
  ]

  def __init__(self):
    """Initializes a parser object."""
    super(XChatLogParser, self).__init__()
    self._last_month = 0
    self._xchat_year = None
    self.offset = 0

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: contains:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
    """
    month, day, hours, minutes, seconds = structure.date_time

    month = timelib.MONTH_DICT.get(month.lower(), 0)

    if month != 0 and month < self._last_month:
      # Gap detected between years.
      self._xchat_year += 1

    return (self._xchat_year, month, day, hours, minutes, seconds)

  def _ParseHeader(self, parser_mediator, structure):
    """Parses a log header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    _, month, day, hours, minutes, seconds, year = structure.date_time

    month = timelib.MONTH_DICT.get(month.lower(), 0)

    time_elements_tuple = (year, month, day, hours, minutes, seconds)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid date time value: {0!s}'.format(structure.date_time))
      return

    self._last_month = month

    event_data = XChatLogEventData()

    if structure.log_action[0] == u'BEGIN':
      self._xchat_year = year
      event_data.text = u'XChat start logging'

    elif structure.log_action[0] == u'END':
      self._xchat_year = None
      event_data.text = u'XChat end logging'

    else:
      logging.debug(u'Unknown log action: {0:s}.'.format(
          u' '.join(structure.log_action)))
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    if not self._xchat_year:
      return

    time_elements_tuple = self._GetTimeElementsTuple(structure)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid date time value: {0!s}'.format(structure.date_time))
      return

    self._last_month = time_elements_tuple[1]

    event_data = XChatLogEventData()
    event_data.nickname = structure.nickname
    # The text string contains multiple unnecessary whitespaces that need to
    # be removed, thus the split and re-join.
    event_data.text = u' '.join(structure.text.split())

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
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
    if key not in (u'header', u'header_signature', u'logline'):
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == u'logline':
      self._ParseLogLine(parser_mediator, structure)

    elif key == u'header':
      self._ParseHeader(parser_mediator, structure)

    elif key == u'header_signature':
      # If this key is matched (after others keys failed) we got a different
      # localized header and we should stop parsing until a new good header
      # is found. Stop parsing is done setting xchat_year to 0.
      # Note that the code assumes that LINE_STRUCTURES will be used in the
      # exact order as defined!
      logging.warning(u'Unknown locale header.')
      self._xchat_year = 0

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a XChat log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (bytes): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    try:
      structure = self._HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a XChat log file')
      return False

    _, month, day, hours, minutes, seconds, year = structure.date_time

    month = timelib.MONTH_DICT.get(month.lower(), 0)

    time_elements_tuple = (year, month, day, hours, minutes, seconds)

    try:
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logging.debug(
          u'Not a XChat log file, invalid date and time: {0!s}'.format(
              structure.date_time))
      return False

    return True


manager.ParsersManager.RegisterParser(XChatLogParser)
