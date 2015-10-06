# -*- coding: utf-8 -*-
"""This file contains XChat scrollback log file parser in plaso.

Information updated 06 September 2013.

Besides the logging capability, the XChat IRC client has the option to
record the text for opened tabs. So, when rejoining a particular channel
and/or a particular conversation, XChat will display the last messages
exchanged. This artifact could be present, if not disabled, even if
normal logging is disabled.

From the XChat FAQ (http://xchatdata.net/Using/FAQ):

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

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatScrollbackEvent(time_events.PosixTimeEvent):
  """Convenience class for a XChat Scrollback line event."""
  DATA_TYPE = u'xchat:scrollback:line'

  def __init__(self, posix_time, offset, nickname, text):
    """Initializes the event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      offset: The offset of the event.
      nickname: The nickname used.
      text: The text sent by nickname or other text (server, messages, etc.).
    """
    super(XChatScrollbackEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.ADDED_TIME)
    self.offset = offset
    self.nickname = nickname
    self.text = text


class XChatScrollbackParser(text_parser.PyparsingSingleLineTextParser):
  """Parse XChat scrollback log files."""

  NAME = u'xchatscrollback'
  DESCRIPTION = u'Parser for XChat scrollback log files.'

  _ENCODING = u'UTF-8'

  # Define how a log line should look like.
  LOG_LINE = (
      pyparsing.Literal(u'T').suppress() +
      pyparsing.Word(pyparsing.nums).setResultsName(u'timestamp') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName(u'text'))
  LOG_LINE.parseWithTabs()

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'logline', LOG_LINE),
  ]

  # Define for the stripping phase.
  STRIPPER = (
      pyparsing.Word(u'\x03', pyparsing.nums, max=3).suppress() |
      pyparsing.Word(u'\x02\x07\x08\x0f\x16\x1d\x1f', exact=1).suppress())

  # Define the structure for parsing <text> and get <nickname> and <text>
  MSG_NICK_START = pyparsing.Literal(u'<')
  MSG_NICK_END = pyparsing.Literal(u'>')
  MSG_NICK = pyparsing.SkipTo(MSG_NICK_END).setResultsName(u'nickname')
  MSG_ENTRY_NICK = pyparsing.Optional(MSG_NICK_START + MSG_NICK + MSG_NICK_END)
  MSG_ENTRY_TEXT = pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName(u'text')
  MSG_ENTRY = MSG_ENTRY_NICK + MSG_ENTRY_TEXT
  MSG_ENTRY.parseWithTabs()

  def __init__(self):
    """Initializes a parser object."""
    super(XChatScrollbackParser, self).__init__()
    self.use_local_zone = False
    self.offset = 0

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a XChat scrollback log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    structure = self.LOG_LINE

    try:
      parsed_structure = structure.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a XChat scrollback log file')
      return False

    try:
      posix_time = int(parsed_structure.timestamp)
    except ValueError:
      logging.debug(
          u'Not a XChat scrollback log file, invalid timestamp string')
      return False

    if not timelib.Timestamp.FromPosixTime(posix_time):
      logging.debug(u'Not a XChat scrollback log file, invalid timestamp')
      return False

    return True

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key != u'logline':
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))
      return

    try:
      posix_time = int(structure.timestamp)
    except ValueError:
      logging.debug(u'Invalid timestamp string {0:s}, skipping record'.format(
          structure.timestamp))
      return

    try:
      nickname, text = self._StripThenGetNicknameAndText(structure.text)
    except pyparsing.ParseException:
      logging.debug(u'Error parsing entry at offset {0:d}'.format(self.offset))
      return

    event_object = XChatScrollbackEvent(posix_time, self.offset, nickname, text)
    parser_mediator.ProduceEvent(event_object)

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
      text: The text obtained from the record entry.

    Returns:
      A list containing two entries:
        nickname: The nickname if present.
        text: The text written by nickname or service messages.
    """
    stripped = self.STRIPPER.transformString(text)
    structure = self.MSG_ENTRY.parseString(stripped)
    text = structure.text.replace(u'\t', u' ')
    return structure.nickname, text


manager.ParsersManager.RegisterParser(XChatScrollbackParser)
