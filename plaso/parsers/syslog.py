# -*- coding: utf-8 -*-
"""This file contains a syslog parser in plaso."""

from plaso.events import text_events
from plaso.lib import lexer
from plaso.lib import utils
from plaso.parsers import manager
from plaso.parsers import text_parser


class SyslogLineEvent(text_events.TextEvent):
  """Convenience class for a syslog line event."""
  DATA_TYPE = u'syslog:line'


class SyslogParser(text_parser.SlowLexicalTextParser):
  """Parse text based syslog files."""

  NAME = u'syslog'
  DESCRIPTION = u'Parser for syslog files.'

  # TODO: can we change this similar to SQLite where create an
  # event specific object for different lines using a callback function.
  # Define the tokens that make up the structure of a syslog file.
  tokens = [
      lexer.Token(
          u'INITIAL', u'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) ',
          u'SetMonth', u'DAY'),
      lexer.Token(u'DAY', r'\s?(\d{1,2})\s+', u'SetDay', u'TIME'),
      lexer.Token(u'TIME', r'([0-9:\.]+) ', u'SetTime', u'STRING_HOST'),
      lexer.Token(u'STRING_HOST', r'^--(-)', u'ParseHostname', u'STRING'),
      lexer.Token(
          u'STRING_HOST', r'([^\s]+) ', u'ParseHostname', u'STRING_PID'),
      lexer.Token(u'STRING_PID', r'([^\:\n]+)', u'ParsePid', u'STRING'),
      lexer.Token(u'STRING', r'([^\n]+)', u'ParseString', u''),
      lexer.Token(u'STRING', r'\n\t', None, u''),
      lexer.Token(u'STRING', r'\t', None, u''),
      lexer.Token(u'STRING', r'\n', u'ParseMessage', u'INITIAL'),
      lexer.Token(u'.', r'([^\n]+)\n', u'ParseIncomplete', u'INITIAL'),
      lexer.Token(u'.', r'\n[^\t]', u'ParseIncomplete', u'INITIAL'),
      lexer.Token(u'S[.]+', r'(.+)', u'ParseString', u''),
      ]

  def __init__(self):
    """Initializes a syslog parser object."""
    super(SyslogParser, self).__init__(local_zone=True)
    # Set the initial year to 0 (fixed in the actual Parse method)
    self._year_use = 0
    self._last_month = 0

    # Set some additional attributes.
    self.attributes[u'reporter'] = u''
    self.attributes[u'pid'] = u''

  def ParseLine(self, parser_mediator):
    """Parse a single line from the syslog file.

    This method extends the one from TextParser slightly, adding
    the context of the reporter and pid values found inside syslog
    files.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    # Note this an older comment applying to a similar approach previously
    # the init function.
    # TODO: this is a HACK to get the tests working let's discuss this.
    if not self._year_use:
      self._year_use = parser_mediator.year

    if not self._year_use:
      # TODO: Find a decent way to actually calculate the correct year
      # instead of relying on stats object.
      self._year_use = parser_mediator.GetFileEntryYear()

      if not self._year_use:
        # TODO: Make this sensible, not have the year permanent.
        self._year_use = 2012

    month_compare = int(self.attributes[u'imonth'])
    if month_compare and self._last_month > month_compare:
      self._year_use += 1

    self._last_month = int(self.attributes[u'imonth'])

    self.attributes[u'iyear'] = self._year_use

    super(SyslogParser, self).ParseLine(parser_mediator)

  def ParseHostname(self, match=None, **unused_kwargs):
    """Parses the hostname.

       This is a callback function for the text parser (lexer) and is
       called by the STRING_HOST lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes[u'hostname'] = match.group(1)

  def ParsePid(self, match=None, **unused_kwargs):
    """Parses the process identifier (PID).

       This is a callback function for the text parser (lexer) and is
       called by the STRING_PID lexer state.

    Args:
      match: The regular expression match object.
    """
    # TODO: Change this logic and rather add more Tokens that
    # fully cover all variations of the various PID stages.
    line = match.group(1)
    if line[-1] == ']':
      splits = line.split(u'[')
      if len(splits) == 2:
        self.attributes[u'reporter'], pid = splits
      else:
        pid = splits[-1]
        self.attributes[u'reporter'] = u'['.join(splits[:-1])
      try:
        self.attributes[u'pid'] = int(pid[:-1])
      except ValueError:
        self.attributes[u'pid'] = 0
    else:
      self.attributes[u'reporter'] = line

  def ParseString(self, match=None, **unused_kwargs):
    """Parses a (body text) string.

       This is a callback function for the text parser (lexer) and is
       called by the STRING lexer state.

    Args:
      match: The regular expression match object.
    """
    self.attributes[u'body'] += utils.GetUnicodeString(match.group(1))

  def PrintLine(self):
    """Prints a log line."""
    self.attributes[u'iyear'] = 2012
    return super(SyslogParser, self).PrintLine()

  # TODO: this is a rough initial implementation to get this working.
  def CreateEvent(self, timestamp, offset, attributes):
    """Creates a syslog line event.

       This overrides the default function in TextParser to create
       syslog line events instead of text events.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the event.
      attributes: A dict that contains the events attributes.

    Returns:
      A text event (SyslogLineEvent).
    """
    return SyslogLineEvent(timestamp, offset, attributes)


manager.ParsersManager.RegisterParser(SyslogParser)
