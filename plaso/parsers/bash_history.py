# -*- coding: utf-8 -*-
"""Parser for bash history files."""
import re

import pyparsing

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import manager
from plaso.parsers import text_parser


class BashEvent(time_events.PosixTimeEvent):
  """Convenience class for events from a ProdBash history file."""

  DATA_TYPE = u'bash:history:command'

  def __init__(self, timestamp, command):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value, epoch.
      command: The command that was run
    """
    super(BashEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.command = command


class BashParser(text_parser.PyparsingMultiLineTextParser):
  """Parses event from Bash history on production machines."""

  NAME = u'bash'
  DESCRIPTION = u'Parser for Bash history files'

  # Matches timestamps between ~2001 and ~2033, by which time this code
  # has hopefully been deprecated.
  TIMESTAMP = pyparsing.Suppress('#') + pyparsing.Word(
      pyparsing.nums, exact=10).setParseAction(
          text_parser.PyParseIntCast).setResultsName(u'timestamp')
  COMMAND = pyparsing.Regex(
      r'.*?(?=($|\n#\d{10}))', re.DOTALL).setResultsName(u'command')
  LINE_GRAMMAR = TIMESTAMP + COMMAND + pyparsing.lineEnd()
  VERIFICATION_GRAMMAR = (pyparsing.Regex(r'^\s?[^#].*?$', re.MULTILINE) +
                          TIMESTAMP +
                          pyparsing.NotAny(pyparsing.pythonStyleComment))
  LINE_STRUCTURES = [(u'log_entry', LINE_GRAMMAR)]

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a bash history file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    matches = self.VERIFICATION_GRAMMAR.scanString(line, maxMatches=1)
    if list(matches):
      return True


  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a Bash history event.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: an string indicating the name of the parsed structure.
      structure: the elements parsed from the file (instance of
                 pyparsing.ParseResults).

    Raises:
      UnableToParseFile: if an unsupported key is provided.
    """
    if key == u'log_entry':
      event_object = BashEvent(structure.timestamp, structure.command)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(BashParser)
