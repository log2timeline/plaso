# -*- coding: utf-8 -*-
"""This file contains SELinux log file parser in plaso.

   Information updated 16 january 2013.

   The parser applies to SELinux 'audit.log' file.
   An entry log file example is the following:

   type=AVC msg=audit(1105758604.519:420): avc: denied { getattr } for pid=5962
   comm="httpd" path="/home/auser/public_html" dev=sdb2 ino=921135

   The Parser will extract the 'type' value, the timestamp abd the 'pid'.
   In the previous example, the timestamp is '1105758604.519', and it
   represents the EPOCH time (seconds since Jan 1, 1970) plus the
   milliseconds past current time (epoch: 1105758604, milliseconds: 519).

   The number after the timestamp (420 in the example) is a 'serial number'
   that can be used to correlate multiple logs generated from the same event.

   References
   http://selinuxproject.org/page/NB_AL
   http://blog.commandlinekungfu.com/2010/08/episode-106-epoch-fail.html
   http://www.redhat.com/promo/summit/2010/presentations/
   taste_of_training/Summit_2010_SELinux.pdf
"""

import logging
import re

from plaso.events import text_events
from plaso.lib import errors
from plaso.lib import lexer
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxLineEvent(text_events.TextEvent):
  """Convenience class for a SELinux log line event."""
  DATA_TYPE = u'selinux:line'


class SELinuxParser(text_parser.SlowLexicalTextParser):
  """Parse SELinux audit log files."""

  NAME = u'selinux'
  DESCRIPTION = u'Parser for SELinux audit log files.'

  PID_RE = re.compile(r'pid=([0-9]+)[\s]+', re.DOTALL)

  tokens = [
      # Skipping empty lines, both EOLs are considered here and in other states.
      lexer.Token(u'INITIAL', r'^\r?\n', '', ''),
      # FSM entry point ('type=anything msg=audit'), critical to recognize a
      # SELinux audit file and used to retrieve the audit type. From there two
      # next states are possible: TIME or failure, since TIME state is required.
      # An empty type is not accepted and it will cause a failure.
      # Examples:
      #   type=SYSCALL msg=audit(...): ...
      #   type=UNKNOWN[1323] msg=audit(...): ...
      lexer.Token(
          u'INITIAL', r'^type=([\w]+(\[[0-9]+\])?)[ \t]+msg=audit',
          u'ParseType', u'TIMESTAMP'),
      lexer.Token(
          u'TIMESTAMP', r'\(([0-9]+)\.([0-9]+):([0-9]*)\):', u'ParseTime',
          u'STRING'),
      # Get the log entry description and stay in the same state.
      lexer.Token(u'STRING', r'[ \t]*([^\r\n]+)', u'ParseString', u''),
      # Entry parsed. Note that an empty description is managed and it will not
      # raise a parsing failure.
      lexer.Token(u'STRING', r'[ \t]*\r?\n', u'ParseMessage', u'INITIAL'),
      # The entry is not formatted as expected, so the parsing failed.
      lexer.Token(u'.', r'([^\r\n]+)\r?\n', u'ParseFailed', u'INITIAL')
  ]

  def __init__(self):
    """Initializes a parser object."""
    # Set local_zone to false, since timestamps are UTC.
    super(SELinuxParser, self).__init__(local_zone=False)
    self.attributes = {u'audit_type': u'', u'pid': u'', u'body': u''}
    self.timestamp = 0

  def ParseType(self, match=None, **unused_kwargs):
    """Parse the audit event type.

    Args:
      match: The regular expression match object.
    """
    self.attributes[u'audit_type'] = match.group(1)

  def ParseTime(self, match=None, **unused_kwargs):
    """Parse the log timestamp.

    Args:
      match: The regular expression match object.
    """
    # TODO: do something with match.group(3) ?
    try:
      number_of_seconds = int(match.group(1), 10)
      timestamp = timelib.Timestamp.FromPosixTime(number_of_seconds)
      timestamp += int(match.group(2), 10) * 1000
      self.timestamp = timestamp
    except ValueError as exception:
      logging.error(
          u'Unable to retrieve timestamp with error: {0:s}'.format(exception))
      self.timestamp = 0
      raise errors.ParseError(u'Not a valid timestamp.')

  def ParseString(self, match=None, **unused_kwargs):
    """Add a string to the body attribute.

    This method extends the one from TextParser slightly,
    searching for the 'pid=[0-9]+' value inside the message body.

    Args:
      match: The regular expression match object.
    """
    try:
      self.attributes[u'body'] += match.group(1)
      # TODO: fix it using lexer or remove pid parsing.
      # Indeed this is something that lexer is able to manage, but 'pid' field
      # is non positional: so, by doing the following step, the FSM is kept
      # simpler. Left the 'to do' as a reminder of possible refactoring.
      pid_search = self.PID_RE.search(self.attributes[u'body'])
      if pid_search:
        self.attributes[u'pid'] = pid_search.group(1)
    except IndexError:
      self.attributes[u'body'] += match.group(0).strip(u'\n')

  def ParseFailed(self, **unused_kwargs):
    """Entry parsing failed callback."""
    raise errors.ParseError(u'Unable to parse SELinux log line.')

  def ParseLine(self, parser_mediator):
    """Parse a single line from the SELinux audit file.

    This method extends the one from TextParser slightly, creating a
    SELinux event with the timestamp (UTC) taken from log entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      TimestampError: if timestamp is not defined.
    """
    if not self.timestamp:
      raise errors.TimestampError(
          u'Unable to parse log line - missing timestamp.')

    offset = getattr(self, u'entry_offset', 0)
    event_object = SELinuxLineEvent(self.timestamp, offset, self.attributes)
    parser_mediator.ProduceEvent(event_object)
    self.timestamp = 0


manager.ParsersManager.RegisterParser(SELinuxParser)
