# -*- coding: utf-8 -*-
"""Parser for bash history files."""

import re

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class BashHistoryEventData(events.EventData):
  """Bash history log event data.

  Attributes:
    command (str): command that was executed.
  """

  DATA_TYPE = 'bash:history:command'

  def __init__(self):
    """Initializes event data."""
    super(BashHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None


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

  LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a Bash history event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key != 'log_entry':
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    event_data = BashHistoryEventData()
    event_data.command = self._GetValueFromStructure(structure, 'command')

    timestamp = self._GetValueFromStructure(structure, 'timestamp')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a bash history file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    match_generator = self._VERIFICATION_GRAMMAR.scanString(lines, maxMatches=1)
    return bool(list(match_generator))


manager.ParsersManager.RegisterParser(BashHistoryParser)
