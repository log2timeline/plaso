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
from plaso.parsers import text_parser


class ZshHistoryEvent(time_events.PosixTimeEvent):
  """Convenience class for Zsh history events."""
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
    self.elapsed_seconds = elapsed_seconds
    self.command = command


class ZshExtendedHistoryParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Zsh extended_history files"""

  NAME = u'zsh_extended_history'
  DESCRIPTION = u'Parser for ZSH extended history files'

  VERIFICATION_REGEX = re.compile(r'^:\s\d+:\d+;')

  _pyparsing_components = {
      u'timestamp': text_parser.PyparsingConstants.INTEGER.setResultsName(
          u'timestamp'),
      u'elapsed_seconds': text_parser.PyparsingConstants.INTEGER.setResultsName(
          u'elapsed_seconds'),
      u'command':  pyparsing.Regex(r'.+?(?=($|\n:\s\d+:\d+;))', re.DOTALL).
          setResultsName(u'command'),
  }

  LINE_GRAMMAR = (
      pyparsing.Literal(u':') +
      _pyparsing_components[u'timestamp'] + pyparsing.Literal(u':') +
      _pyparsing_components[u'elapsed_seconds'] + pyparsing.Literal(u';') +
      _pyparsing_components[u'command'] + pyparsing.LineEnd())

  LINE_STRUCTURES = [(u'line', LINE_GRAMMAR)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return a Zsh history event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Raises:
      UnableToParseFile: if an unexpected key is provided.
    """
    if key != u'line':
      raise errors.UnableToParseFile(u'Unrecognized key {0:s}'.format(key))

    event_object = ZshHistoryEvent(
        structure[u'timestamp'], structure[u'elapsed_seconds'],
        structure[u'command'])
    parser_mediator.ProduceEvent(event_object)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies whether content corresponds to a Zsh extended_history file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      lines: A buffer containing lines from a log file.

    Returns:
      Returns a boolean that indicates the lines appear to contain content from
       a Zsh extended_history file.
    """
    if self.VERIFICATION_REGEX.match(lines):
      return True