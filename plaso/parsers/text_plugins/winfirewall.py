# -*- coding: utf-8 -*-
"""Text parser plugin for Windows Firewall Log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class WinFirewallEventData(events.EventData):
  """Windows Firewall event data.

  Attributes:
    action (str): action taken.
    destination_ip (str): destination IP address.
    destination_port (int): TCP or UDP destination port.
    icmp_code (int): ICMP code.
    icmp_type (int): ICMP type.
    information (str): additional information.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    packet_size (int): packet size.
    path (str): direction of the communication, which can be: SEND, RECEIVE,
        FORWARD, and UNKNOWN.
    protocol (str): IP protocol.
    source_ip (str): source IP address.
    source_port (int): TCP or UDP source port.
    tcp_ack (int): TCP acknowledgement number.
    tcp_flags (str): TCP flags.
    tcp_sequence_number (int): TCP sequence number.
    tcp_window_size (int): TCP window size.
  """

  DATA_TYPE = 'windows:firewall_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(WinFirewallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.destination_ip = None
    self.destination_port = None
    self.icmp_code = None
    self.icmp_type = None
    self.information = None
    self.last_written_time = None
    self.packet_size = None
    self.path = None
    self.protocol = None
    self.source_ip = None
    self.source_port = None
    self.tcp_ack = None
    self.tcp_flags = None
    self.tcp_sequence_number = None
    self.tcp_window_size = None


class WinFirewallLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Windows Firewall Log files."""

  NAME = 'winfirewall'
  DATA_FORMAT = 'Windows Firewall log file'

  ENCODING = 'ascii'

  _BLANK = pyparsing.Suppress(pyparsing.Literal('-'))

  _WORD = (
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Word(pyparsing.alphanums + '-', min=2) |
      _BLANK)

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.ConvertTokenToInteger) | _BLANK

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _DATE = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS)

  _TIME = pyparsing.Group(
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS)

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address | _BLANK)

  _PORT_NUMBER = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      text_parser.ConvertTokenToInteger) | _BLANK

  _COMMENT_LINE = pyparsing.Literal('#') + pyparsing.SkipTo(pyparsing.LineEnd())

  # Version 1.5 fields:
  # date time action protocol src-ip dst-ip src-port dst-port size tcpflags
  # tcpsyn tcpack tcpwin icmptype icmpcode info path

  _LOG_LINE_1_5 = (
      _DATE.setResultsName('date') +
      _TIME.setResultsName('time') +
      _WORD.setResultsName('action') +
      _WORD.setResultsName('protocol') +
      _IP_ADDRESS.setResultsName('source_ip') +
      _IP_ADDRESS.setResultsName('destination_ip') +
      _PORT_NUMBER.setResultsName('source_port') +
      _PORT_NUMBER.setResultsName('destination_port') +
      _INTEGER.setResultsName('packet_size') +
      _WORD.setResultsName('tcp_flags') +
      _INTEGER.setResultsName('tcp_sequence_number') +
      _INTEGER.setResultsName('tcp_ack') +
      _INTEGER.setResultsName('tcp_window_size') +
      _INTEGER.setResultsName('icmp_type') +
      _INTEGER.setResultsName('icmp_code') +
      _WORD.setResultsName('information') +
      _WORD.setResultsName('path'))

  _LOG_LINE_STRUCTURES = {}

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.

  _LOG_LINE_STRUCTURES['date'] = _DATE.setResultsName('date')
  _LOG_LINE_STRUCTURES['time'] = _TIME.setResultsName('time')
  _LOG_LINE_STRUCTURES['action'] = _WORD.setResultsName('action')
  _LOG_LINE_STRUCTURES['protocol'] = _WORD.setResultsName('protocol')
  _LOG_LINE_STRUCTURES['src-ip'] = _IP_ADDRESS.setResultsName('source_ip')
  _LOG_LINE_STRUCTURES['dst-ip'] = _IP_ADDRESS.setResultsName('destination_ip')
  _LOG_LINE_STRUCTURES['src-port'] = _PORT_NUMBER.setResultsName('source_port')
  _LOG_LINE_STRUCTURES['dst-port'] = _PORT_NUMBER.setResultsName(
      'destination_port')
  _LOG_LINE_STRUCTURES['size'] = _INTEGER.setResultsName('packet_size')
  _LOG_LINE_STRUCTURES['tcpflags'] = _WORD.setResultsName('tcp_flags')
  _LOG_LINE_STRUCTURES['tcpsyn'] = _INTEGER.setResultsName(
      'tcp_sequence_number')
  _LOG_LINE_STRUCTURES['tcpack'] = _INTEGER.setResultsName('tcp_ack')
  _LOG_LINE_STRUCTURES['tcpwin'] = _INTEGER.setResultsName('tcp_window_size')
  _LOG_LINE_STRUCTURES['icmptype'] = _INTEGER.setResultsName('icmp_type')
  _LOG_LINE_STRUCTURES['icmpcode'] = _INTEGER.setResultsName('icmp_code')
  _LOG_LINE_STRUCTURES['info'] = _WORD.setResultsName('information')
  _LOG_LINE_STRUCTURES['path'] = _WORD.setResultsName('path')

  _LINE_STRUCTURES = [
      ('comment', _COMMENT_LINE),
      ('logline', _LOG_LINE_1_5)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a text parser plugin."""
    super(WinFirewallLogTextPlugin, self).__init__()
    self._use_local_time = False

  def _ParseCommentLine(self, parser_mediator, structure):
    """Parses a comment line.

    Args:
      structure (pyparsing.ParseResults): parsed log line.
    """
    comment = structure[1]

    if comment == 'Fields:':
      self._ParseFieldsMetadata(parser_mediator, structure)

    if comment.startswith('Time Format'):
      _, _, time_format = comment.partition(':')
      self._use_local_time = 'local' in time_format.lower()

  def _ParseFieldsMetadata(self, parser_mediator, structure):
    """Parses the fields metadata and updates the log line definition to match.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    fields = self._GetValueFromStructure(structure, 'fields', default_value='')
    fields = fields.strip()
    fields = fields.split(' ')

    log_line_structure = pyparsing.Empty()
    for member in fields:
      if not member:
        continue

      field_structure = self._LOG_LINE_STRUCTURES.get(member, None)
      if not field_structure:
        field_structure = self._WORD
        parser_mediator.ProduceExtractionWarning(
            'missing definition for field: {0:s} defaulting to WORD'.format(
                member))

      log_line_structure += field_structure

    line_structures = [
        ('comment', self._COMMENT_LINE),
        ('logline', log_line_structure)]
    self._SetLineStructures(line_structures)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
    """
    event_data = WinFirewallEventData()
    event_data.action = self._GetValueFromStructure(structure, 'action')
    event_data.destination_ip = self._GetValueFromStructure(
        structure, 'destination_ip')
    event_data.destination_port = self._GetValueFromStructure(
        structure, 'destination_port')
    event_data.icmp_code = self._GetValueFromStructure(structure, 'icmp_code')
    event_data.icmp_type = self._GetValueFromStructure(structure, 'icmp_type')
    event_data.information = self._GetValueFromStructure(
        structure, 'information')
    event_data.last_written_time = self._ParseTimeElements(structure)
    event_data.path = self._GetValueFromStructure(structure, 'path')
    event_data.protocol = self._GetValueFromStructure(structure, 'protocol')
    event_data.packet_size = self._GetValueFromStructure(
        structure, 'packet_size')
    event_data.source_ip = self._GetValueFromStructure(structure, 'source_ip')
    event_data.source_port = self._GetValueFromStructure(
        structure, 'source_port')
    event_data.tcp_ack = self._GetValueFromStructure(structure, 'tcp_ack')
    event_data.tcp_flags = self._GetValueFromStructure(structure, 'tcp_flags')
    event_data.tcp_sequence_number = self._GetValueFromStructure(
        structure, 'tcp_sequence_number')
    event_data.tcp_window_size = self._GetValueFromStructure(
        structure, 'tcp_window_size')

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      try:
        self._ParseLogLine(parser_mediator, structure)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line with error: {0!s}'.format(exception))

    elif key == 'comment':
      self._ParseCommentLine(parser_mediator, structure)

  def _ParseTimeElements(self, structure):
    """Parses date and time elements of a log line.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      date_elements_structure = self._GetValueFromStructure(structure, 'date')
      time_elements_structure = self._GetValueFromStructure(structure, 'time')

      year, month, day_of_month = date_elements_structure
      hours, minutes, seconds = time_elements_structure

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = self._use_local_time

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ResetState(self):
    """Resets stored values."""
    self._use_local_time = False

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    found_signature = False
    while line and line[0] == '#':
      if line.startswith('#Software: Microsoft Windows Firewall'):
        found_signature = True
        break

      try:
        line = self._ReadLineOfText(text_file_object)
      except UnicodeDecodeError:
        break

    if not found_signature:
      return False

    self._ResetState()

    return True


text_parser.SingleLineTextParser.RegisterPlugin(WinFirewallLogTextPlugin)
