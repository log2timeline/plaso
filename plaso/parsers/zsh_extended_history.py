# -*- coding: utf-8 -*-
"""Parser for Zsh extended_history files.

The file format is described here:
http://zsh.sourceforge.net/Doc/Release/Options.html#index-EXTENDEDHISTORY
"""
import re

import pyparsing

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import manager
from plaso.parsers import text_parser


class ZshHistoryEvent(time_events.PosixTimeEvent):
  """Convenience class for Zsh history events.

  Attributes:
    command: a string containing the command that was run.
    elapsed_seconds: an integer containing the time in seconds that the
                     command took to execute.
  """
  DATA_TYPE = u'shell:zsh:history'

  def __init__(self, posix_time, elapsed_seconds, command):
    """Initializes an event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      elapsed_seconds: an integer containing the time in seconds the command
                    took to execute.
      command: a string containing the command that was run.
    """
    super(ZshHistoryEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.MODIFICATION_TIME)
    self.command = command
    self.elapsed_seconds = elapsed_seconds


class ZshExtendedHistoryParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Zsh extended_history files"""

  NAME = u'zsh_extended_history'
  DESCRIPTION = u'Parser for ZSH extended history files'

  _VERIFICATION_REGEX = re.compile(r'^:\s\d+:\d+;')

  _PYPARSING_COMPONENTS = {
      u'timestamp': text_parser.PyparsingConstants.INTEGER.
                    setResultsName(u'timestamp'),
      u'elapsed_seconds': text_parser.PyparsingConstants.INTEGER.
                          setResultsName(u'elapsed_seconds'),
      u'command': pyparsing.Regex(r'.+?(?=($|\n:\s\d+:\d+;))', re.DOTALL).
                  setResultsName(u'command'),
  }

  _LINE_GRAMMAR = (
      pyparsing.Literal(u':') +
      _PYPARSING_COMPONENTS[u'timestamp'] + pyparsing.Literal(u':') +
      _PYPARSING_COMPONENTS[u'elapsed_seconds'] + pyparsing.Literal(u';') +
      _PYPARSING_COMPONENTS[u'command'] + pyparsing.LineEnd())

  LINE_STRUCTURES = [(u'command', _LINE_GRAMMAR)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a Zsh history event.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: an string indicating the name of the parsed structure.
      structure: the elements parsed from the file (instance of
                 pyparsing.ParseResults).

    Raises:
      UnableToParseFile: if an unsupported key is provided.
    """
    if key != u'command':
      raise errors.UnableToParseFile(u'Unsupported key {0:s}'.format(key))

    event_object = ZshHistoryEvent(
        structure[u'timestamp'], structure[u'elapsed_seconds'],
        structure[u'command'])
    parser_mediator.ProduceEvent(event_object)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies whether content corresponds to a Zsh extended_history file.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      lines: a string containing one or more lines of content from the file-like
             object being evaluated for parsing.

    Returns:
      A boolean that indicates the lines appear to contain content from a
      Zsh extended_history file.
    """
    if self._VERIFICATION_REGEX.match(lines):
      return True


manager.ParsersManager.RegisterParser(ZshExtendedHistoryParser)
