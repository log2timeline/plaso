# -*- coding: utf-8 -*-
"""Parser for Zsh extended_history files.

The file format is described here:
http://zsh.sourceforge.net/Doc/Release/Options.html#index-EXTENDEDHISTORY
"""

from __future__ import unicode_literals

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
  """Zsh history event data.

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
  """Parser for Zsh extended_history files"""

  NAME = 'zsh_extended_history'
  DESCRIPTION = 'Parser for ZSH extended history files'

  _ENCODING = 'utf-8'

  _VERIFICATION_REGEX = re.compile(r'^:\s\d+:\d+;')

  _PYPARSING_COMPONENTS = {
      'timestamp': text_parser.PyparsingConstants.INTEGER.setResultsName(
          'timestamp'),
      'elapsed_seconds': text_parser.PyparsingConstants.INTEGER.setResultsName(
          'elapsed_seconds'),
      'command': pyparsing.Regex(
          r'.+?(?=($|\n:\s\d+:\d+;))', re.DOTALL).setResultsName('command'),
  }

  _LINE_GRAMMAR = (
      pyparsing.Literal(':') +
      _PYPARSING_COMPONENTS['timestamp'] + pyparsing.Literal(':') +
      _PYPARSING_COMPONENTS['elapsed_seconds'] + pyparsing.Literal(';') +
      _PYPARSING_COMPONENTS['command'] + pyparsing.LineEnd())

  LINE_STRUCTURES = [('command', _LINE_GRAMMAR)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a Zsh history event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key != 'command':
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
    """Verifies whether content corresponds to a Zsh extended_history file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    if self._VERIFICATION_REGEX.match(lines):
      return True

    return False

manager.ParsersManager.RegisterParser(ZshExtendedHistoryParser)
