# -*- coding: utf-8 -*-
"""Parser for ZSH extended_history files.

References:
  https://zsh.sourceforge.io/Doc/Release/Options.html#index-EXTENDEDHISTORY
"""

import re

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class ZshHistoryEventData(events.EventData):
  """ZSH history event data.

  Attributes:
    command (str): command that was run.
    elapsed_seconds (int): number of seconds that the command took to execute.
  """
  DATA_TYPE = 'shell:zsh:history'

  def __init__(self):
    """Initializes event data."""
    super(ZshHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.elapsed_seconds = None


class ZshExtendedHistoryParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for ZSH extended history files"""

  NAME = 'zsh_extended_history'
  DATA_FORMAT = 'ZSH extended history file'

  _ENCODING = 'utf-8'

  _VERIFICATION_REGEX = re.compile(r'^:\s\d+:\d+;')

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _COMMAND = pyparsing.Regex(
      r'.+?(?=($|\n:\s\d+:\d+;))', re.DOTALL).setResultsName('command')

  _LINE_GRAMMAR = (
      pyparsing.Literal(':') + _INTEGER.setResultsName('timestamp') +
      pyparsing.Literal(':') + _INTEGER.setResultsName('elapsed_seconds') +
      pyparsing.Literal(';') + _COMMAND + pyparsing.LineEnd())

  LINE_STRUCTURES = [('command', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a ZSH history event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    event_data = ZshHistoryEventData()
    event_data.command = self._GetValueFromStructure(structure, 'command')
    event_data.elapsed_seconds = self._GetValueFromStructure(
        structure, 'elapsed_seconds')

    timestamp = self._GetValueFromStructure(structure, 'timestamp')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies whether content corresponds to a ZSH extended_history file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    return bool(self._VERIFICATION_REGEX.match(lines))


manager.ParsersManager.RegisterParser(ZshExtendedHistoryParser)
