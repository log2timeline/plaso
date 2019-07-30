# -*- coding: utf-8 -*-
"""Parser for Windows Firewall Log file."""

from __future__ import unicode_literals

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser

import pytz  # pylint: disable=wrong-import-order


class WinFirewallEventData(events.EventData):
  """Windows Firewall event data.

  Attributes:
    action (str): action taken.
    protocol (str): IP protocol.
    source_ip (str): source IP address.
    dest_ip (str): destination IP address.
    source_port (int): TCP or UDP source port.
    dest_port (int): TCP or UDP destination port.
    size (int): size of ???
    flags (str): TCP flags.
    tcp_seq (int): TCP sequence number.
    tcp_ack (int): TCP ACK ???
    tcp_win (int): TCP window size ???
    icmp_type (int): ICMP type.
    icmp_code (int): ICMP code.
    info (str): ???
    path (str): ???
  """

  DATA_TYPE = 'windows:firewall:log_entry'

  def __init__(self):
    """Initializes event data."""
    super(WinFirewallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.dest_ip = None
    self.dest_port = None
    self.flags = None
    self.icmp_code = None
    self.icmp_type = None
    self.info = None
    self.path = None
    self.protocol = None
    self.size = None
    self.source_ip = None
    self.source_port = None
    self.tcp_ack = None
    self.tcp_seq = None
    self.tcp_win = None


class WinFirewallParser(text_parser.PyparsingSingleLineTextParser):
  """Parses the Windows Firewall Log file."""

  NAME = 'winfirewall'
  DESCRIPTION = 'Parser for Windows Firewall Log files.'

  _ENCODING = 'ascii'

  # TODO: Add support for custom field names. Currently this parser only
  # supports the default fields, which are:
  #   date time action protocol src-ip dst-ip src-port dst-port size
  #   tcpflags tcpsyn tcpack tcpwin icmptype icmpcode info path

  _BLANK = pyparsing.Suppress(pyparsing.Literal('-'))

  _WORD = (
      pyparsing.Word(pyparsing.alphanums, min=1) |
      pyparsing.Word(pyparsing.alphanums + '-', min=2) |
      _BLANK)

  _INTEGER = (
      pyparsing.Word(pyparsing.nums, min=1).setParseAction(
          text_parser.ConvertTokenToInteger) |
      _BLANK)

  _IP_ADDRESS = (
      text_parser.PyparsingConstants.IPV4_ADDRESS |
      text_parser.PyparsingConstants.IPV6_ADDRESS |
      _BLANK)

  _PORT_NUMBER = (
      pyparsing.Word(pyparsing.nums, min=1, max=6).setParseAction(
          text_parser.ConvertTokenToInteger) |
      _BLANK)

  _LOG_LINE = (
      text_parser.PyparsingConstants.DATE_TIME.setResultsName('date_time') +
      _WORD.setResultsName('action') +
      _WORD.setResultsName('protocol') +
      _IP_ADDRESS.setResultsName('source_ip') +
      _IP_ADDRESS.setResultsName('dest_ip') +
      _PORT_NUMBER.setResultsName('source_port') +
      _PORT_NUMBER.setResultsName('dest_port') +
      _INTEGER.setResultsName('size') +
      _WORD.setResultsName('flags') +
      _INTEGER.setResultsName('tcp_seq') +
      _INTEGER.setResultsName('tcp_ack') +
      _INTEGER.setResultsName('tcp_win') +
      _INTEGER.setResultsName('icmp_type') +
      _INTEGER.setResultsName('icmp_code') +
      _WORD.setResultsName('info') +
      _WORD.setResultsName('path'))

  LINE_STRUCTURES = [
      ('comment', text_parser.PyparsingConstants.COMMENT_LINE_HASH),
      ('logline', _LOG_LINE),
  ]

  def __init__(self):
    """Initializes a parser object."""
    super(WinFirewallParser, self).__init__()
    self._software = None
    self._use_local_timezone = False
    self._version = None

  def _ParseCommentRecord(self, structure):
    """Parse a comment and store appropriate attributes.

    Args:
      structure (pyparsing.ParseResults): parsed log line.
    """
    comment = structure[1]
    if comment.startswith('Version'):
      _, _, self._version = comment.partition(':')
    elif comment.startswith('Software'):
      _, _, self._software = comment.partition(':')
    elif comment.startswith('Time'):
      _, _, time_format = comment.partition(':')
      if 'local' in time_format.lower():
        self._use_local_timezone = True

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = WinFirewallEventData()
    event_data.action = self._GetValueFromStructure(structure, 'action')
    event_data.dest_ip = self._GetValueFromStructure(structure, 'dest_ip')
    event_data.dest_port = self._GetValueFromStructure(structure, 'dest_port')
    event_data.flags = self._GetValueFromStructure(structure, 'flags')
    event_data.icmp_code = self._GetValueFromStructure(structure, 'icmp_code')
    event_data.icmp_type = self._GetValueFromStructure(structure, 'icmp_type')
    event_data.info = self._GetValueFromStructure(structure, 'info')
    event_data.path = self._GetValueFromStructure(structure, 'path')
    event_data.protocol = self._GetValueFromStructure(structure, 'protocol')
    event_data.size = self._GetValueFromStructure(structure, 'size')
    event_data.source_ip = self._GetValueFromStructure(structure, 'source_ip')
    event_data.source_port = self._GetValueFromStructure(
        structure, 'source_port')
    event_data.tcp_ack = self._GetValueFromStructure(structure, 'tcp_ack')
    event_data.tcp_seq = self._GetValueFromStructure(structure, 'tcp_seq')
    event_data.tcp_win = self._GetValueFromStructure(structure, 'tcp_win')

    if self._use_local_timezone:
      time_zone = parser_mediator.timezone
    else:
      time_zone = pytz.UTC

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN, time_zone=time_zone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): identifier of the structure of tokens.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in ('comment', 'logline'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'comment':
      self._ParseCommentRecord(structure)

    elif key == 'logline':
      self._ParseLogLine(parser_mediator, structure)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a firewall log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """
    # TODO: Examine other versions of the file format and if this parser should
    # support them.
    stripped_line = line.rstrip()
    return stripped_line == '#Version: 1.5'


manager.ParsersManager.RegisterParser(WinFirewallParser)
