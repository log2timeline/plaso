# -*- coding: utf-8 -*-
"""Text parser plugin for bash history files."""

import re

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
# from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class BashHistoryEventData(events.EventData):
  """Bash history log event data.

  Attributes:
    command (str): command that was executed.
    written_time (dfdatetime.DateTimeValues): date and time the entry was
        written.
  """

  DATA_TYPE = 'bash:history:entry'

  def __init__(self):
    """Initializes event data."""
    super(BashHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.written_time = None


class BashHistoryTextPlugin(interface.TextPlugin):
  """Text parser plugin for bash history files."""

  NAME = 'bash_history'

  DATA_FORMAT = 'Bash history file'

  ENCODING = 'utf-8'

  _TIMESTAMP = (
      pyparsing.Suppress('#') +
      pyparsing.Word(pyparsing.nums, min=9, max=10).setParseAction(
          lambda tokens: int(tokens[0], 10)).setResultsName('timestamp'))

  _COMMAND = pyparsing.Regex(
      r'.*?(?=($|\n#\d{10}))', re.DOTALL).setResultsName('command')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = _TIMESTAMP + _COMMAND + _END_OF_LINE

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = (
      pyparsing.Regex(r'^\s?[^#].*?$', re.MULTILINE) + _TIMESTAMP +
      pyparsing.NotAny(pyparsing.pythonStyleComment))

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

    event_data = BashHistoryEventData()
    event_data.command = self._GetValueFromStructure(structure, 'command')
    event_data.written_time = dfdatetime_posix_time.PosixTime(
        timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      # TODO: refactor
      # structure, _, _ = self._VerifyString(text_reader.lines)
      match_generator = self.VERIFICATION_GRAMMAR.scanString(
          text_reader.lines, maxMatches=1)
      return bool(list(match_generator))

    # except errors.ParseError:
    except pyparsing.ParseException:
      return False


text_parser.TextLogParser.RegisterPlugin(BashHistoryTextPlugin)
