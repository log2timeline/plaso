# -*- coding: utf-8 -*-
"""Text parser plugin for Snort3/Suricata fast-log alert log files.

Snort3/Suricata fast.log format is a single line log format as shown below.
The following variants are known:

  Snort3:
    Month/Day-Hour:Minute:Second:FractionOfSeconds [**] [sid] "string" [**] \\
    [Classification: string] [Priority : int] {protocol} \\
    SOURCE_IP:SOURCE_PORT -> DESTINATION_IP:DESTINATION_PORT

  Suricata:
    Year/Month/Day-Hour:Minute:Second:FractionOfSeconds [**] [sid] string \\
    [**] [Classification: string] [Priority : int] {protocol} \\
    SOURCE_IP:SOURCE_PORT -> DESTINATION_IP:DESTINATION_PORT

Also see:
  https://suricata.readthedocs.io/en/suricata-6.0.0/configuration/suricata-yaml.html#line-based-alerts-log-fast-log
"""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import regular_expressions
from plaso.lib import yearless_helper
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SnortFastAlertEventData(events.EventData):
  """Snort3/Suricata fast-log alert event data.

  Attributes:
    classification (str): classification of the alert.
    destination_ip (str): destination IP-address.
    destination_port (int): destination TCP/UDP port number.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    message (str): message associated with the alert.
    priority (int): priorty, ranging from 1 (high) to 4 (very low).
    rule_identifier (str): identifier of the Snort3/Suricata rule that generated
        the alert.
    source_ip (str): source IP-address.
    source_port (int): source TCP/UDP port number.
  """

  DATA_TYPE = 'snort:fastlog:alert'

  def __init__(self):
    """Initializes event data."""
    super(SnortFastAlertEventData, self).__init__(data_type=self.DATA_TYPE)
    self.classification = None
    self.destination_ip = None
    self.destination_port = None
    self.last_written_time = None
    self.message = None
    self.priority = None
    self.protocol = None
    self.rule_identifier = None
    self.source_ip = None
    self.source_port = None


class SnortFastLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for Snort3/Suricata fast-log alert log files."""

  NAME = 'snort_fastlog'
  DATA_FORMAT = 'Snort3/Suricata fast-log alert log (fast.log) file'

  # TODO: remove after refactoring.
  _SINGLE_LINE_MODE = True

  _VERIFICATION_REGEX = re.compile(''.join([
      # Date: "MM/DD" and "YY/MM/DD"
      r'^(\d{2}\/)?\d{2}\/\d{2}\-\d{2}:\d{2}:\d{2}.\d{6}\s*',
      r'\[\*\*\]\s*',  # Separator ([**])
      r'\[\d*:\d*:\d*\]\s*',  # Rule identifier
      r'"?.*\"?\s*\[\*\*\]\s*',  # Message
      r'(\[Classification:\s.*\])?\s*',  # Optional Classification
      r'(\[Priority\:\s*\d{1}\])?\s*',  # Optional Priority
      r'\{\w+\}\s*',  # Procotol
      regular_expressions.IP_ADDRESS,  # Source IPv4 or IPv6 address
      r'(:\d*)?\s*',  # Optional TCP/UDP source port
      r'\-\>\s*',  # Separator '->'
      regular_expressions.IP_ADDRESS,  # Destination IPv4 or IPv6 address
      r'(:\d*)?$']))  # Optional TCP/UDP destination port

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      text_parser.PyParseIntCast)

  _DATE_MONTH_DAY = (
      _TWO_DIGITS + pyparsing.Suppress('/') + _TWO_DIGITS)

  _DATE_YEAR_MONTH_DAY = (
      _TWO_DIGITS + pyparsing.Suppress('/') + _DATE_MONTH_DAY)

  # Date and time values are formatted as: MM/DD-hh:mm:ss.###### or
  # YY/MM/DD-hh:mm:ss.######
  # For example: 12/28-12:55:38.765402 or 10/05/10-10:08:59.667372
  _DATE_TIME = (
      (_DATE_YEAR_MONTH_DAY | _DATE_MONTH_DAY) + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') + _SIX_DIGITS)

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address)

  _MESSAGE = pyparsing.Combine(pyparsing.OneOrMore(
      pyparsing.Word(pyparsing.printables, excludeChars='["') |
      pyparsing.White(' ', max=2))).setResultsName('message')

  _RULE_IDENTIFIER = pyparsing.Combine(
      _INTEGER + ':' + _INTEGER + ':' + _INTEGER).setResultsName(
          'rule_identifier')

  _FASTLOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Suppress('[**] [') + _RULE_IDENTIFIER +
      pyparsing.Suppress('] ') + pyparsing.Optional(pyparsing.Suppress('"')) +
      _MESSAGE + pyparsing.Optional(pyparsing.Suppress('"')) +
      pyparsing.Suppress('[**]') +
      pyparsing.Optional(
          pyparsing.Suppress(pyparsing.Literal('[Classification:')) +
          pyparsing.Regex('[^]]*').setResultsName('classification') +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(
          pyparsing.Suppress('[Priority:') +
          _INTEGER.setResultsName('priority') +
          pyparsing.Suppress(']')) +
      pyparsing.Suppress('{') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('protocol') +
      pyparsing.Suppress('}') +
      _IP_ADDRESS.setResultsName('source_ip_address') +
      pyparsing.Optional(
          pyparsing.Suppress(':') +
          _INTEGER.setResultsName('source_port')) +
      pyparsing.Suppress('->') +
      _IP_ADDRESS.setResultsName('destination_ip_address') +
      pyparsing.Optional(
          pyparsing.Suppress(':') +
          _INTEGER.setResultsName('destination_port')) +
      pyparsing.Suppress(pyparsing.lineEnd()))

  _LINE_STRUCTURES = [('fastlog_line', _FASTLOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = SnortFastAlertEventData()
    event_data.classification = self._GetValueFromStructure(
        structure, 'classification')
    event_data.destination_ip = self._GetValueFromStructure(
        structure, 'destination_ip_address')
    event_data.destination_port = self._GetValueFromStructure(
        structure, 'destination_port')
    event_data.last_written_time = self._ParseTimeElements(
        time_elements_structure)
    event_data.message = self._GetStringValueFromStructure(structure, 'message')
    event_data.priority = self._GetValueFromStructure(structure, 'priority')
    event_data.protocol = self._GetValueFromStructure(structure, 'protocol')
    event_data.source_ip = self._GetValueFromStructure(
        structure, 'source_ip_address')
    event_data.source_port = self._GetValueFromStructure(
        structure, 'source_port')
    event_data.rule_identifier = self._GetValueFromStructure(
        structure, 'rule_identifier')

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      has_year = len(time_elements_structure) == 7

      if has_year:
        year, month, day_of_month, hours, minutes, seconds, microseconds = (
            time_elements_structure)

        year += 2000
      else:
        month, day_of_month, hours, minutes, seconds, microseconds = (
            time_elements_structure)

        self._UpdateYear(month)

        year = self._GetRelativeYear()

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, microseconds)

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          is_delta=(not has_year), time_elements_tuple=time_elements_tuple)

      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    line = text_reader.ReadLine()

    if not self._VERIFICATION_REGEX.match(line):
      return False

    self._SetEstimatedYear(parser_mediator)

    return True


text_parser.SingleLineTextParser.RegisterPlugin(SnortFastLogTextPlugin)
