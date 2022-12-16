# -*- coding: utf-8 -*-
"""Text parser plugin for XChat scrollback log files.

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
<T><space><decimal timestamp><space><text><\\n>

The time reported in the log is the number of seconds since January 1, 1970
00:00:00 UTC (from source code, time(0)). The <text> part could contain some
'decorators' (bold, underline, colors indication, etc.), so the parser
should strip those control fields.

Also see:
  http://xchat.org
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class XChatScrollbackEventData(events.EventData):
  """XChat Scrollback line event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    nickname (str): nickname.
    text (str): text sent by nickname service messages.
  """

  DATA_TYPE = 'xchat:scrollback:line'

  def __init__(self):
    """Initializes event data."""
    super(XChatScrollbackEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.nickname = None
    self.text = None


class XChatScrollbackLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for XChat scrollback log files."""

  NAME = 'xchatscrollback'
  DATA_FORMAT = 'XChat scrollback log file'

  ENCODING = 'utf-8'

  # Using a regular expression to include checking for spaces.
  _LOG_LINE = pyparsing.Regex(r'T (?P<timestamp>\d{1,10}) (?P<raw_text>.*)\n')

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

  # Define for the stripping phase.
  _STRIPPER = (
      pyparsing.Word('\x03', pyparsing.nums, max=3).suppress() |
      pyparsing.Word('\x02\x07\x08\x0f\x16\x1d\x1f', exact=1).suppress())

  _NICKNAME = pyparsing.QuotedString('<', endQuoteChar='>').setResultsName(
      'nickname')

  # Define the structure for parsing <text> and get <nickname> and <text>
  _MESSAGE = (pyparsing.Optional(_NICKNAME) +
              pyparsing.restOfLine().setResultsName('text')).parseWithTabs()

  def _ParseRawText(self, raw_text):
    """Parses the raw text.

    This method implements the XChat strip_color2 and fe_print_text
    functions, slightly modified to get pure text. From the parsing point
    of view, after having stripped, the code takes everything as is,
    simply replacing tabs with spaces (as the original XChat code).

    Args:
      raw_text (str): raw text obtained from the log record.

    Returns:
      tuple[str, str]: nickname and text, or None if not available.

    Raises:
      ParseError: if the raw text cannot be parsed.
    """
    try:
      stripped_text = self._STRIPPER.transformString(raw_text)
      structure = self._MESSAGE.parseString(stripped_text)
    except pyparsing.ParseException as exception:
      raise errors.ParseError(
          'Unable to parse raw text with error: {0!s}'.format(exception))

    nickname = self._GetValueFromStructure(structure, 'nickname')
    text = self._GetValueFromStructure(structure, 'text', default_value='')
    text = text.replace('\t', ' ')
    return nickname, text

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
    timestamp = self._GetValueFromStructure(structure, 'timestamp')
    timestamp = int(timestamp, 10)

    raw_text = self._GetValueFromStructure(
        structure, 'raw_text', default_value='')

    nickname, text = self._ParseRawText(raw_text)

    event_data = XChatScrollbackEventData()
    event_data.added_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event_data.nickname = nickname
    event_data.text = text

    parser_mediator.ProduceEventData(event_data)

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
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(XChatScrollbackLogTextPlugin)
