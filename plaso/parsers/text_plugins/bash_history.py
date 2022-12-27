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


class BashHistoryTextPlugin(interface.TextPlugin):
  """Text parser plugin for bash history files."""

  NAME = 'bash_history'

  DATA_FORMAT = 'Bash history file'

  ENCODING = 'utf-8'

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _TIMESTAMP_LINE = pyparsing.Regex(r'#(?P<timestamp>[1-9][0-9]{8,9})\n')

  _COMMAND_LINE = (
      pyparsing.restOfLine().setResultsName('command') + _END_OF_LINE)

  _LOG_LINE = _TIMESTAMP_LINE + _COMMAND_LINE

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  # A desynchronized bash history file will start with the command line
  # instead of the timestamp.
  VERIFICATION_GRAMMAR = (
      (_TIMESTAMP_LINE + _COMMAND_LINE) ^
      (_COMMAND_LINE + _TIMESTAMP_LINE + _COMMAND_LINE))

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
    timestamp = self._GetDecimalValueFromStructure(structure, 'timestamp')

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
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(BashHistoryTextPlugin)
