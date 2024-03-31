# -*- coding: utf-8 -*-
"""Text parser plugin for bash history files."""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
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


class BashHistoryTextPlugin(interface.TextPluginWithLineContinuation):
  """Text parser plugin for bash history files."""

  NAME = 'bash_history'

  DATA_FORMAT = 'Bash history file'

  ENCODING = 'utf-8'

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _TIMESTAMP_LINE = pyparsing.Regex(r'#(?P<timestamp>[1-9][0-9]{8,9})\n')

  _COMMAND_LINE = (
      pyparsing.restOfLine().set_results_name('command') + _END_OF_LINE)

  _LINE_STRUCTURES = [('timestamp_line', _TIMESTAMP_LINE)]

  # A desynchronized bash history file will start with the command line
  # instead of the timestamp.
  VERIFICATION_GRAMMAR = (
      (_TIMESTAMP_LINE + _COMMAND_LINE) ^
      (_COMMAND_LINE + _TIMESTAMP_LINE + _COMMAND_LINE))

  def __init__(self):
    """Initializes a text parser plugin."""
    super(BashHistoryTextPlugin, self).__init__()
    self._command_lines = None
    self._event_data = None

  def _ParseFinalize(self, parser_mediator):
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    if self._event_data:
      self._event_data.command = ' '.join(self._command_lines)
      self._command_lines = []

      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

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
    if key == '_line_continuation':
      # A desynchronized bash history file will start with the command line
      # instead of the timestamp.
      if not self._event_data:
        self._event_data = BashHistoryEventData()

      command = structure.replace('\n', ' ').strip()
      self._command_lines.append(command)

    else:
      if self._event_data:
        self._event_data.command = ' '.join(self._command_lines)

        parser_mediator.ProduceEventData(self._event_data)

      timestamp = self._GetDecimalValueFromStructure(structure, 'timestamp')

      self._event_data = BashHistoryEventData()
      self._event_data.written_time = dfdatetime_posix_time.PosixTime(
          timestamp=timestamp)
      self._command_lines = []

  def _ResetState(self):
    """Resets stored values."""
    self._command_lines = []
    self._event_data = None

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct plugin, False otherwise.
    """
    try:
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(BashHistoryTextPlugin)
