# -*- coding: utf-8 -*-
"""Parser for bash history files."""

import re

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


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


class BashHistoryParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from Bash history files."""

  NAME = 'bash_history'

  DATA_FORMAT = 'Bash history file'

  _ENCODING = 'utf-8'

  _TIMESTAMP = pyparsing.Suppress('#') + pyparsing.Word(
      pyparsing.nums, min=9, max=10).setParseAction(
          text_parser.PyParseIntCast).setResultsName('timestamp')

  _COMMAND = pyparsing.Regex(
      r'.*?(?=($|\n#\d{10}))', re.DOTALL).setResultsName('command')

  _LINE_GRAMMAR = _TIMESTAMP + _COMMAND + pyparsing.lineEnd()

  _VERIFICATION_GRAMMAR = (
      pyparsing.Regex(r'^\s?[^#].*?$', re.MULTILINE) + _TIMESTAMP +
      pyparsing.NotAny(pyparsing.pythonStyleComment))

  _LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    match_generator = self._VERIFICATION_GRAMMAR.scanString(
        text_reader.lines, maxMatches=1)
    return bool(list(match_generator))

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a Bash history event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    timestamp = self._GetValueFromStructure(structure, 'timestamp')

    event_data = BashHistoryEventData()
    event_data.command = self._GetValueFromStructure(structure, 'command')
    event_data.written_time = dfdatetime_posix_time.PosixTime(
        timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(BashHistoryParser)
