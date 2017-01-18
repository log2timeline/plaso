# -*- coding: utf-8 -*-
"""Parser for bash history files."""
import re

import pyparsing

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import manager
from plaso.parsers import text_parser


class BashHistoryEvent(time_events.PosixTimeEvent):
  """Convenience class for events from a Bash history file."""

  DATA_TYPE = u'bash:history:command'

  def __init__(self, timestamp, command):
    """Initializes the event object.

    Args:
      timestamp (int): number of seconds after January 1, 1970, 00:00:00 UTC
          that the command was run.
      command (str): command that was executed.
    """
    super(BashHistoryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.command = command


class BashHistoryParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from Bash history files."""

  NAME = u'bash'

  DESCRIPTION = u'Parser for Bash history files'

  _ENCODING = u'utf-8'

  # Matches timestamps between ~2001 and ~2033, by which time this code
  # has hopefully been deprecated.
  _TIMESTAMP = pyparsing.Suppress(u'#') + pyparsing.Word(
      pyparsing.nums, exact=10).setParseAction(
          text_parser.PyParseIntCast).setResultsName(u'timestamp')

  _COMMAND = pyparsing.Regex(
      r'.*?(?=($|\n#\d{10}))', re.DOTALL).setResultsName(u'command')

  _LINE_GRAMMAR = _TIMESTAMP + _COMMAND + pyparsing.lineEnd()

  _VERIFICATION_GRAMMAR = (
    pyparsing.Regex(r'^\s?[^#].*?$', re.MULTILINE) + _TIMESTAMP +
    pyparsing.NotAny(pyparsing.pythonStyleComment))

  LINE_STRUCTURES = [(u'log_entry', _LINE_GRAMMAR)]

  def ParseRecord(self, mediator, key, structure):
    """Parses a record and produces a Bash history event.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      UnableToParseFile: if an unsupported key is provided.
    """
    if key == u'log_entry':
      event_object = BashHistoryEvent(structure.timestamp, structure.command)
      mediator.ProduceEvent(event_object)
    else:
      raise errors.UnableToParseFile(u'Unsupported key: {0:s}'.format(key))

  def VerifyStructure(self, unused_mediator, line):
    """Verifies that this is a bash history file.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      line (str): single line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    matches = self._VERIFICATION_GRAMMAR.scanString(line, maxMatches=1)
    if list(matches):
      return True


manager.ParsersManager.RegisterParser(BashHistoryParser)
