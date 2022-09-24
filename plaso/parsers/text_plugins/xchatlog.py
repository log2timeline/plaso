# -*- coding: utf-8 -*-
"""Text parser plugin for XChat log files.

Information updated 24 July 2013.

The parser applies to XChat log files. Despite their apparent
simplicity it's not straightforward to manage every possible case.
XChat tool allows users to specify how timestamp will be
encoded (using the strftime function), by letting them specify
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

Moreover the strftime is locale-dependent, so month names, footer and
headers can change, even inside the same log file. Being said that, the
following will be the main logic used to parse the log files (note that
the first header *must be* '\\*\\*\\*\\* BEGIN ...' otherwise file will be
skipped).

1) Check for '\\*\\*\\*\\*'
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
2) Not '\\*\\*\\*\\*' so we are parsing a line
2.1) If parsing = True, try to parse line and generate event
2.2) If parsing = False, skip until next good header is found

References
http://xchat.org
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class XChatLogEventData(events.EventData):
  """XChat Log event data.

  Attributes:
    nickname (str): nickname.
    text (str): text sent by nickname or other text (server, messages, etc.).
  """

  DATA_TYPE = 'xchat:log:line'

  def __init__(self):
    """Initializes event data."""
    super(XChatLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.nickname = None
    self.text = None


class XChatLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for XChat log files."""

  NAME = 'xchatlog'
  DATA_FORMAT = 'XChat log file'

  ENCODING = 'utf-8'

  # Common (header/footer/body) pyparsing structures.

  # TODO: Only English ASCII timestamp supported ATM, add support for others.

  _WEEKDAY = pyparsing.Group(
      pyparsing.Keyword('Sun') |
      pyparsing.Keyword('Mon') |
      pyparsing.Keyword('Tue') |
      pyparsing.Keyword('Wed') |
      pyparsing.Keyword('Thu') |
      pyparsing.Keyword('Fri') |
      pyparsing.Keyword('Sat'))

  # Header/footer pyparsing structures.
  # Sample: "**** BEGIN LOGGING AT Mon Dec 31 21:11:55 2011".
  # Note that "BEGIN LOGGING" text is localized (default, English) and can be
  # different if XChat locale is different.

  _HEADER_SIGNATURE = pyparsing.Keyword('****')
  _HEADER_DATE_TIME = pyparsing.Group(
      _WEEKDAY.setResultsName('weekday') +
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          'day_of_month') +
      text_parser.PyparsingConstants.TIME_ELEMENTS +
      text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName('year'))
  _LOG_ACTION = pyparsing.Group(
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables))
  _HEADER = (
      _HEADER_SIGNATURE.suppress() + _LOG_ACTION.setResultsName('log_action') +
      _HEADER_DATE_TIME.setResultsName('date_time'))

  # Body (nickname, text and/or service messages) pyparsing structures.
  # Sample: "dec 31 21:11:58 <fpi> ola plas-ing guys!".

  _DATE_TIME = pyparsing.Group(
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          'day_of_month') +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  _NICKNAME = pyparsing.QuotedString('<', endQuoteChar='>').setResultsName(
      'nickname')

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Optional(_NICKNAME) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  _LINE_STRUCTURES = [
      ('logline', _LOG_LINE),
      ('header', _HEADER),
      ('header_signature', _HEADER_SIGNATURE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')

    if len(time_elements_tuple) == 5:
      month_string, day_of_month, hours, minutes, seconds = time_elements_tuple

      month = self._GetMonthFromString(month_string)

      self._UpdateYear(month)

      year = self._GetYear()

    else:
      _, month_string, day_of_month, hours, minutes, seconds, year = (
          time_elements_tuple)

      month = self._GetMonthFromString(month_string)

      self._SetMonthAndYear(month, year)

    return year, month, day_of_month, hours, minutes, seconds

  def _ParseHeader(self, parser_mediator, structure):
    """Parses a log header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    try:
      time_elements_tuple = self._GetTimeElementsTuple(structure)
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      self._year = None
      return

    log_action = self._GetValueFromStructure(
        structure, 'log_action', default_value=[])

    if log_action[0] not in ('BEGIN', 'END'):
      parser_mediator.ProduceExtractionWarning(
          'unsupported log action: {0:s}.'.format(' '.join(log_action)))
      self._year = None
      return

    event_data = XChatLogEventData()

    if log_action[0] == 'BEGIN':
      event_data.text = 'XChat start logging'
    else:
      event_data.text = 'XChat end logging'
      self._year = None

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    if not self._year:
      return

    try:
      time_elements_tuple = self._GetTimeElementsTuple(structure)
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      return

    text = self._GetValueFromStructure(structure, 'text')
    # The text string contains multiple unnecessary whitespaces that need to
    # be removed, thus the split and re-join.
    text = ' '.join(text.split())

    event_data = XChatLogEventData()
    event_data.nickname = self._GetValueFromStructure(structure, 'nickname')
    event_data.text = text

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      self._ParseLogLine(parser_mediator, structure)

    elif key == 'header':
      self._ParseHeader(parser_mediator, structure)

    elif key == 'header_signature':
      # If this key is matched (after others keys failed) we got a different
      # localized header and we should stop parsing until a new good header
      # is found.
      parser_mediator.ProduceExtractionWarning('unsupported locale header')
      self._year = None

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    try:
      parsed_structure = self._HEADER.parseString(line)
    except pyparsing.ParseException:
      return False

    try:
      time_elements_tuple = self._GetTimeElementsTuple(parsed_structure)
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except (TypeError, ValueError):
      return False

    self._year = None

    return True


text_parser.SingleLineTextParser.RegisterPlugin(XChatLogTextPlugin)
