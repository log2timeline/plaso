# -*- coding: utf-8 -*-
"""Parser for Windows Firewall Log file."""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser

import pytz


class WinFirewallParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the Windows Firewall Log file.

  More information can be read here:
    http://technet.microsoft.com/en-us/library/cc758040(v=ws.10).aspx
  """

  NAME = u'winfirewall'
  DESCRIPTION = u'Parser for Windows Firewall Log files.'

  # TODO: Add support for custom field names. Currently this parser only
  # supports the default fields, which are:
  #   date time action protocol src-ip dst-ip src-port dst-port size
  #   tcpflags tcpsyn tcpack tcpwin icmptype icmpcode info path

  # Define common structures.
  BLANK = pyparsing.Literal(u'-')
  WORD = pyparsing.Word(pyparsing.alphanums + u'-') | BLANK
  INT = pyparsing.Word(pyparsing.nums, min=1) | BLANK
  IP = (
      text_parser.PyparsingConstants.IPV4_ADDRESS |
      text_parser.PyparsingConstants.IPV6_ADDRESS | BLANK)
  PORT = pyparsing.Word(pyparsing.nums, min=1, max=6) | BLANK

  # Define how a log line should look like.
  LOG_LINE = (
      text_parser.PyparsingConstants.DATE.setResultsName(u'date') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time') +
      WORD.setResultsName(u'action') + WORD.setResultsName(u'protocol') +
      IP.setResultsName(u'source_ip') + IP.setResultsName(u'dest_ip') +
      PORT.setResultsName(u'source_port') + INT.setResultsName(u'dest_port') +
      INT.setResultsName(u'size') + WORD.setResultsName(u'flags') +
      INT.setResultsName(u'tcp_seq') + INT.setResultsName(u'tcp_ack') +
      INT.setResultsName(u'tcp_win') + INT.setResultsName(u'icmp_type') +
      INT.setResultsName(u'icmp_code') + WORD.setResultsName(u'info') +
      WORD.setResultsName(u'path'))

  # Define the available log line structures.
  LINE_STRUCTURES = [
      (u'comment', text_parser.PyparsingConstants.COMMENT_LINE_HASH),
      (u'logline', LOG_LINE),
  ]

  DATA_TYPE = u'windows:firewall:log_entry'

  def __init__(self):
    """Initializes a parser object."""
    super(WinFirewallParser, self).__init__()
    self._software = None
    self._use_local_zone = False
    self._version = None

  def _ParseCommentRecord(self, structure):
    """Parse a comment and store appropriate attributes.

    Args:
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    comment = structure[1]
    if comment.startswith(u'Version'):
      _, _, self._version = comment.partition(u':')
    elif comment.startswith(u'Software'):
      _, _, self._software = comment.partition(u':')
    elif comment.startswith(u'Time'):
      _, _, time_format = comment.partition(u':')
      if u'local' in time_format.lower():
        self._use_local_zone = True

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    log_dict = structure.asDict()

    date = log_dict.get(u'date', None)
    time = log_dict.get(u'time', None)

    if not date and not time:
      parser_mediator.ProduceParseError(
          u'unable to extract timestamp from logline.')
      return

    if self._use_local_zone:
      zone = parser_mediator.timezone
    else:
      zone = pytz.UTC

    try:
      timestamp = timelib.Timestamp.FromTimeParts(
          date[0], date[1], date[2], time[0], time[1], time[2], timezone=zone)
    except errors.TimestampError as exception:
      parser_mediator.ProduceParseError(
          u'unable to determine timestamp with error: {0:s}'.format(
              exception))
      return

    # TODO: refactor this into a WinFirewall specific event object.
    event_object = time_events.TimestampEvent(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME, self.DATA_TYPE)

    for key, value in log_dict.items():
      if key in (u'time', u'date') or value == u'-':
        continue

      if isinstance(value, pyparsing.ParseResults):
        setattr(event_object, key, u''.join(value))

      else:
        # TODO: determine why this code construction is needed.
        try:
          save_value = int(value)
        except ValueError:
          save_value = value

        setattr(event_object, key, save_value)

    parser_mediator.ProduceEvent(event_object)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    if key == u'comment':
      self._ParseCommentRecord(structure)

    elif key == u'logline':
      self._ParseLogLine(parser_mediator, structure)

    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, unused_parser_mediator, line):
    """Verify that this file is a firewall log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    # TODO: Examine other versions of the file format and if this parser should
    # support them.
    return line == b'#Version: 1.5'


manager.ParsersManager.RegisterParser(WinFirewallParser)
