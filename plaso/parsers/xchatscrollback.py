# -*- coding: utf-8 -*-
"""This file contains XChat scrollback log file parser in plaso.

Information updated 06 September 2013.

Besides the logging capability, the XChat IRC client has the option to
record the text for opened tabs. So, when rejoining a particular channel
and/or a particular conversation, XChat will display the last messages
exchanged. This artifact could be present, if not disabled, even if
normal logging is disabled.

From the XChat FAQ (http://xchat.org/faq):

Q: 'How do I keep text from previous sessions from being displayed when I
join a channel?'
R: 'Starting in XChat 2.8.4, XChat implemented the Scrollback feature which
displays text from the last time you had a particular tab open.
To disable this setting for all channels, Go to Settings -> Preferences
-> Logging and uncheck Display scrollback from previous session.
In XChat 2.8.6, XChat implemented both Per Channel Logging, and
Per Channel Scrollbacks. If you are on 2.8.6 or newer, you can disable
loading scrollback for just one particular tab name by right clicking on
the tab name, selecting Settings, and then unchecking Reload scrollback'

The log file format differs from logging format, but it's quite simple
'T 1232315916 Python interface unloaded'
<T><space><decimal timestamp><space><text><\n>

The time reported in the log is the number of seconds since January 1, 1970
00:00:00 UTC (from source code, time(0)). The <text> part could contain some
'decorators' (bold, underline, colors indication, etc.), so the parser
should strip those control fields.

References
http://xchat.org
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class XChatScrollbackEventData(events.EventData):
  """XChat Scrollback line event data.

  Attributes:
    nickname (str): nickname.
    text (str): text sent by nickname service messages.
  """

  DATA_TYPE = 'xchat:scrollback:line'

  def __init__(self):
    """Initializes event data."""
    super(XChatScrollbackEventData, self).__init__(data_type=self.DATA_TYPE)
    self.nickname = None
    self.text = None


class XChatScrollbackParser(text_parser.PyparsingSingleLineTextParser):
  """Parses XChat scrollback log files."""

  NAME = 'xchatscrollback'
  DATA_FORMAT = 'XChat scrollback log file'

  _ENCODING = 'utf-8'

  # Define how a log line should look like.
  LOG_LINE = (
      pyparsing.Literal('T').suppress() +
      pyparsing.Word(pyparsing.nums).setResultsName('timestamp') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('text'))
  LOG_LINE.parseWithTabs()

  # Define the available log line structures.
  LINE_STRUCTURES = [
      ('logline', LOG_LINE),
  ]

  # Define for the stripping phase.
  STRIPPER = (
      pyparsing.Word('\x03', pyparsing.nums, max=3).suppress() |
      pyparsing.Word('\x02\x07\x08\x0f\x16\x1d\x1f', exact=1).suppress())

  # Define the structure for parsing <text> and get <nickname> and <text>
  MSG_NICK_START = pyparsing.Literal('<')
  MSG_NICK_END = pyparsing.Literal('>')
  MSG_NICK = pyparsing.SkipTo(MSG_NICK_END).setResultsName('nickname')
  MSG_ENTRY_NICK = pyparsing.Optional(MSG_NICK_START + MSG_NICK + MSG_NICK_END)
  MSG_ENTRY_TEXT = pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('text')
  MSG_ENTRY = MSG_ENTRY_NICK + MSG_ENTRY_TEXT
  MSG_ENTRY.parseWithTabs()

  def _StripThenGetNicknameAndText(self, text):
    """Strips decorators from text and gets <nickname> if available.

    This method implements the XChat strip_color2 and fe_print_text
    functions, slightly modified to get pure text. From the parsing point
    of view, after having stripped, the code takes everything as is,
    simply replacing tabs with spaces (as the original XChat code).
    So the VerifyStructure plays an important role in checking if
    the source file has the right format, since the method will not raise
    any parse exception and every content will be good.

    Args:
      text (str): text obtained from the log record.

    Returns:
      tuple: containing:

        nickname (str): nickname.
        text (str): text sent by nickname or service messages.
    """
    stripped = self.STRIPPER.transformString(text)
    structure = self.MSG_ENTRY.parseString(stripped)
    nickname = self._GetValueFromStructure(structure, 'nickname')
    text = self._GetValueFromStructure(structure, 'text', default_value='')
    text = text.replace('\t', ' ')
    return nickname, text

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    if key != 'logline':
      logger.warning(
          'Unable to parse record, unknown structure: {0:s}'.format(key))
      return

    timestamp = self._GetValueFromStructure(structure, 'timestamp')
    try:
      timestamp = int(timestamp, 10)
    except (TypeError, ValueError):
      logger.debug('Invalid timestamp {0!s}, skipping record'.format(timestamp))
      return

    try:
      text = self._GetValueFromStructure(structure, 'text', default_value='')
      nickname, text = self._StripThenGetNicknameAndText(text)
    except pyparsing.ParseException:
      logger.debug('Unable to parse entry')
      return

    event_data = XChatScrollbackEventData()
    event_data.nickname = nickname
    event_data.text = text

    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a XChat scrollback log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    try:
      structure = self.LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      logger.debug('Not a XChat scrollback log file')
      return False

    timestamp = self._GetValueFromStructure(structure, 'timestamp')
    try:
      int(timestamp, 10)
    except (TypeError, ValueError):
      logger.debug('Not a XChat scrollback log file, invalid timestamp.')
      return False

    return True


manager.ParsersManager.RegisterParser(XChatScrollbackParser)
