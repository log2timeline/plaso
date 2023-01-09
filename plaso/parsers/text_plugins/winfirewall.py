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

  # A Windows Firewall is encoded using the system codepage.
  ENCODING = None

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _DATE = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS)

  _TIME = pyparsing.Group(
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS)

  _ACTION = pyparsing.Word(pyparsing.alphanums + '-', min=2)

  _WORD_OR_BLANK = (
      pyparsing.Word(pyparsing.alphanums) | pyparsing.Suppress('-'))

  _IP_ADDRESS_OR_BLANK = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address | pyparsing.Suppress('-'))

  _PORT_NUMBER_OR_BLANK = (
      pyparsing.Word(pyparsing.nums, max=6).setParseAction(
          lambda tokens: int(tokens[0], 10)) | pyparsing.Suppress('-'))

  _INTEGER_OR_BLANK = (
      pyparsing.Word(pyparsing.nums).setParseAction(
          lambda tokens: int(tokens[0], 10)) | pyparsing.Suppress('-'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _FIELDS_METADATA = (
      pyparsing.Suppress('Fields: ') +
      pyparsing.restOfLine().setResultsName('fields'))

  _TIME_FORMAT_METADATA = (
      pyparsing.Suppress('Time Format: ') +
      pyparsing.restOfLine().setResultsName('time_format'))

  _METADATA = (
      _FIELDS_METADATA | _TIME_FORMAT_METADATA | pyparsing.restOfLine())

  _COMMENT_LOG_LINE = pyparsing.Suppress('#') + _METADATA + _END_OF_LINE

  # Version 1.5 fields:
  # date time action protocol src-ip dst-ip src-port dst-port size tcpflags
  # tcpsyn tcpack tcpwin icmptype icmpcode info path

  _LOG_LINE_1_5 = (
      _DATE.setResultsName('date') +
      _TIME.setResultsName('time') +
      _ACTION.setResultsName('action') +
      _WORD_OR_BLANK.setResultsName('protocol') +
      _IP_ADDRESS_OR_BLANK.setResultsName('source_ip') +
      _IP_ADDRESS_OR_BLANK.setResultsName('destination_ip') +
      _PORT_NUMBER_OR_BLANK.setResultsName('source_port') +
      _PORT_NUMBER_OR_BLANK.setResultsName('destination_port') +
      _INTEGER_OR_BLANK.setResultsName('packet_size') +
      _WORD_OR_BLANK.setResultsName('tcp_flags') +
      _INTEGER_OR_BLANK.setResultsName('tcp_sequence_number') +
      _INTEGER_OR_BLANK.setResultsName('tcp_ack') +
      _INTEGER_OR_BLANK.setResultsName('tcp_window_size') +
      _INTEGER_OR_BLANK.setResultsName('icmp_type') +
      _INTEGER_OR_BLANK.setResultsName('icmp_code') +
      _WORD_OR_BLANK.setResultsName('information') +
      _WORD_OR_BLANK.setResultsName('path') +
      _END_OF_LINE)

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.

  _LOG_LINE_STRUCTURES = {
      'action': _ACTION.setResultsName('action'),
      'date': _DATE.setResultsName('date'),
      'dst-ip': _IP_ADDRESS_OR_BLANK.setResultsName('destination_ip'),
      'dst-port': _PORT_NUMBER_OR_BLANK.setResultsName('destination_port'),
      'icmpcode': _INTEGER_OR_BLANK.setResultsName('icmp_code'),
      'icmptype': _INTEGER_OR_BLANK.setResultsName('icmp_type'),
      'info': _WORD_OR_BLANK.setResultsName('information'),
      'path': _WORD_OR_BLANK.setResultsName('path'),
      'protocol': _WORD_OR_BLANK.setResultsName('protocol'),
      'size': _INTEGER_OR_BLANK.setResultsName('packet_size'),
      'src-ip': _IP_ADDRESS_OR_BLANK.setResultsName('source_ip'),
      'src-port': _PORT_NUMBER_OR_BLANK.setResultsName('source_port'),
      'tcpack': _INTEGER_OR_BLANK.setResultsName('tcp_ack'),
      'tcpflags': _WORD_OR_BLANK.setResultsName('tcp_flags'),
      'tcpsyn': _INTEGER_OR_BLANK.setResultsName('tcp_sequence_number'),
      'tcpwin': _INTEGER_OR_BLANK.setResultsName('tcp_window_size'),
      'time': _TIME.setResultsName('time')}

  _HEADER_GRAMMAR = pyparsing.OneOrMore(_COMMENT_LOG_LINE)

  _LINE_STRUCTURES = [('log_line', _LOG_LINE_1_5)]

  VERIFICATION_GRAMMAR = (
      pyparsing.ZeroOrMore(
          pyparsing.Regex('#(Fields|Time Format|Version): .*') + _END_OF_LINE) +
      pyparsing.Regex('#Software: Microsoft Windows Firewall') + _END_OF_LINE)

  VERIFICATION_LITERALS = ['#Software: Microsoft Windows Firewall ']

  def __init__(self):
    """Initializes a text parser plugin."""
    super(WinFirewallLogTextPlugin, self).__init__()
    self._use_local_time = False

  def _ParseFieldsMetadata(self, parser_mediator, fields):
    """Parses the fields metadata and updates the log line definition to match.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      fields (str): field definitions.
    """
    log_line_structure = pyparsing.Empty()
    for member in fields.split(' '):
      if not member:
        continue

      field_structure = self._LOG_LINE_STRUCTURES.get(member, None)
      if not field_structure:
        field_structure = self._WORD_OR_BLANK
        parser_mediator.ProduceExtractionWarning((
            'missing definition for field: {0:s} defaulting to '
            'WORD_OR_BLANK').format(member))

      log_line_structure += field_structure

    log_line_structure += self._END_OF_LINE

    self._SetLineStructures([('log_line', log_line_structure)])

  def _ParseHeader(self, parser_mediator, text_reader):
    """Parses a text-log file header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Raises:
      ParseError: when the header cannot be parsed.
    """
    try:
      structure_generator = self._HEADER_GRAMMAR.scanString(
          text_reader.lines, maxMatches=1)
      structure, start, end = next(structure_generator)

    except StopIteration:
      structure = None

    except pyparsing.ParseException as exception:
      raise errors.ParseError(exception)

    if not structure or start != 0:
      raise errors.ParseError('No match found.')

    fields = self._GetValueFromStructure(structure, 'fields', default_value='')
    fields = fields.strip()
    if fields:
      self._ParseFieldsMetadata(parser_mediator, fields)

    time_format = self._GetValueFromStructure(
        structure, 'time_format', default_value='')
    self._use_local_time = time_format.lower() == 'local'

    text_reader.SkipAhead(end)

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
      ParseError: if the structure cannot be parsed.
    """
    self._ParseLogLine(parser_mediator, structure)

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

    self._SetLineStructures(self._LINE_STRUCTURES)

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(WinFirewallLogTextPlugin)
