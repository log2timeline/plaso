# -*- coding: utf-8 -*-
"""Text parser plugin for ZSH extended_history files.

References:
  https://zsh.sourceforge.io/Doc/Release/Options.html#index-EXTENDEDHISTORY
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class ZshHistoryEventData(events.EventData):
  """ZSH history event data.

  Attributes:
    command (str): command that was run.
    elapsed_seconds (int): number of seconds that the command took to execute.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'shell:zsh:history'

  def __init__(self):
    """Initializes event data."""
    super(ZshHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.elapsed_seconds = None
    self.last_written_time = None


class ZshExtendedHistoryTextPlugin(interface.TextPlugin):
  """Text parser plugin for ZSH extended history files."""

  NAME = 'zsh_extended_history'
  DATA_FORMAT = 'ZSH extended history file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE_START = (
      pyparsing.Literal(':') + _INTEGER.setResultsName('timestamp') +
      pyparsing.Literal(':') + _INTEGER.setResultsName('elapsed_seconds') +
      pyparsing.Literal(';'))

  _LOG_LINE = (
      _LOG_LINE_START + pyparsing.restOfLine().setResultsName('command') +
      _END_OF_LINE)

  _SUCCESSIVE_LOG_LINE = (
      pyparsing.NotAny(_LOG_LINE_START) +
      pyparsing.restOfLine().setResultsName('command') + _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('successive_log_line', _SUCCESSIVE_LOG_LINE)]

  # Using a regular expression here to ensure whitespace is matched accordingly.
  VERIFICATION_GRAMMAR = (
      pyparsing.Regex(r': [0-9]+:[0-9]+;\S') + pyparsing.restOfLine() +
      _END_OF_LINE)

  def __init__(self):
    """Initializes a text parser plugin."""
    super(ZshExtendedHistoryTextPlugin, self).__init__()
    self._event_data = None

  def _ParseFinalize(self, parser_mediator):
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    if self._event_data:
      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

  def _ParseLogline(self, structure):
    """Parses a log line.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    timestamp = self._GetValueFromStructure(structure, 'timestamp')

    event_data = ZshHistoryEventData()
    event_data.command = self._GetValueFromStructure(structure, 'command')
    event_data.elapsed_seconds = self._GetValueFromStructure(
        structure, 'elapsed_seconds')
    event_data.last_written_time = dfdatetime_posix_time.PosixTime(
        timestamp=timestamp)

    self._event_data = event_data

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
    if key == 'log_line':
      if self._event_data:
        parser_mediator.ProduceEventData(self._event_data)
        self._event_data = None

      self._ParseLogline(structure)

    elif key == 'successive_log_line':
      command = self._GetValueFromStructure(
          structure, 'command', default_value='')
      command = command.strip()

      self._event_data.command = ' '.join([self._event_data.command, command])

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
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._event_data = None

    return True


text_parser.TextLogParser.RegisterPlugin(ZshExtendedHistoryTextPlugin)
