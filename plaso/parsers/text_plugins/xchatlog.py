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

Also see:
  http://xchat.org
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class XChatLogEventData(events.EventData):
  """XChat Log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    nickname (str): nickname.
    text (str): text sent by nickname or other text (server, messages, etc.).
  """

  DATA_TYPE = 'xchat:log:line'

  def __init__(self):
    """Initializes event data."""
    super(XChatLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.nickname = None
    self.text = None


class XChatLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for XChat log files."""

  NAME = 'xchatlog'
  DATA_FORMAT = 'XChat log file'

  ENCODING = 'utf-8'

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  # TODO: Only English ASCII timestamp supported ATM, add support for others.

  _WEEKDAY = pyparsing.Group(
      pyparsing.Keyword('Sun') |
      pyparsing.Keyword('Mon') |
      pyparsing.Keyword('Tue') |
      pyparsing.Keyword('Wed') |
      pyparsing.Keyword('Thu') |
      pyparsing.Keyword('Fri') |
      pyparsing.Keyword('Sat'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Header/footer pyparsing structures.
  # Sample: "**** BEGIN LOGGING AT Mon Dec 31 21:11:55 2011".
  # Note that "BEGIN LOGGING" text is localized (default, English) and can be
  # different if XChat locale is different.

  # Header date and time values are formatted as: Mon Dec 31 21:11:55 2011
  _SECTION_HEADER_DATE_TIME = pyparsing.Group(
      _WEEKDAY + _THREE_LETTERS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _FOUR_DIGITS)

  _LOG_ACTION = pyparsing.Group(
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables) +
      pyparsing.Word(pyparsing.printables))

  _SECTION_HEADER_LINE = (
      pyparsing.Suppress('****') + _LOG_ACTION.setResultsName('log_action') +
      _SECTION_HEADER_DATE_TIME.setResultsName('date_time') +
      _END_OF_LINE)

  # Body (nickname, text and/or service messages) pyparsing structures.
  # Sample: "dec 31 21:11:58 <fpi> ola plas-ing guys!".

  # Date and time values are formatted as: dec 31 21:11:58
  _DATE_TIME = pyparsing.Group(
      _THREE_LETTERS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS)

  _NICKNAME = pyparsing.QuotedString('<', endQuoteChar='>').setResultsName(
      'nickname')

  _CHAT_HISTORY_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Optional(_NICKNAME) +
      pyparsing.restOfLine().setResultsName('text') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('chat_history_line', _CHAT_HISTORY_LINE),
      ('section_header_line', _SECTION_HEADER_LINE)]

  VERIFICATION_GRAMMAR = _SECTION_HEADER_LINE

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    text = self._GetValueFromStructure(structure, 'text')
    # The text string contains multiple unnecessary whitespaces that need to
    # be removed, thus the split and re-join.
    text = ' '.join(text.split())

    event_data = XChatLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.nickname = self._GetValueFromStructure(structure, 'nickname')
    event_data.text = text

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    if key == 'chat_history_line':
      self._ParseLogLine(parser_mediator, structure)

    elif key == 'section_header_line':
      self._ParseSectionHeaderLine(parser_mediator, structure)

  def _ParseSectionHeaderLine(self, parser_mediator, structure):
    """Parses a section header line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    log_action = self._GetValueFromStructure(
        structure, 'log_action', default_value=[])

    if log_action[0] not in ('BEGIN', 'END'):
      parser_mediator.ProduceExtractionWarning(
          'unsupported log action: {0:s}.'.format(' '.join(log_action)))
      self._year = None
      return

    event_data = XChatLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)

    if log_action[0] == 'BEGIN':
      event_data.text = 'XChat start logging'
    else:
      event_data.text = 'XChat end logging'
      self._year = None

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      if len(time_elements_structure) == 5:
        month_string, day_of_month, hours, minutes, seconds = (
            time_elements_structure)

        month = self._GetMonthFromString(month_string)

        # Use year-less helper to ensure a change in year is accounted for.
        self._UpdateYear(month)

        year = self._GetYear()

      else:
        _, month_string, day_of_month, hours, minutes, seconds, year = (
            time_elements_structure)

        month = self._GetMonthFromString(month_string)

        self._SetMonthAndYear(month, year)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._year = None

    return True


text_parser.TextLogParser.RegisterPlugin(XChatLogTextPlugin)
