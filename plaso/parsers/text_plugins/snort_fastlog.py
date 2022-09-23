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
from plaso.containers import time_events
from plaso.lib import definitions
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
    self.message = None
    self.priority = None
    self.protocol = None
    self.rule_identifier = None
    self.source_ip = None
    self.source_port = None


class SnortFastLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for Snort3/Suricata fast-log alert log files."""

  NAME = 'snort:fastlog:alert'
  DATA_FORMAT = 'Snort3/Suricata fast-log alert log (fast.log) file'

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

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      text_parser.PyParseIntCast)

  _DATE_MONTH_DAY = (
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('/') +
      _TWO_DIGITS.setResultsName('day_of_month'))

  _DATE_YEAR_MONTH_DAY = (
      _TWO_DIGITS.setResultsName('year') + pyparsing.Suppress('/') +
      _DATE_MONTH_DAY)

  _DATE_TIME = (
      (_DATE_YEAR_MONTH_DAY | _DATE_MONTH_DAY) +
      pyparsing.Suppress(text_parser.PyparsingConstants.HYPHEN) +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') + pyparsing.Suppress('.') +
      _SIX_DIGITS.setResultsName('microseconds'))

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address)

  _MESSAGE = pyparsing.Combine(pyparsing.OneOrMore(
      pyparsing.Word(pyparsing.printables, excludeChars='["') |
      pyparsing.White(' ', max=2))).setResultsName('message')

  _RULE_IDENTIFIER = pyparsing.Combine(
      text_parser.PyparsingConstants.INTEGER + ':' +
      text_parser.PyparsingConstants.INTEGER + ':' +
      text_parser.PyparsingConstants.INTEGER).setResultsName('rule_identifier')

  _FASTLOG_LINE = (
      _DATE_TIME + pyparsing.Suppress('[**] [') + _RULE_IDENTIFIER +
      pyparsing.Suppress('] ') + pyparsing.Optional(pyparsing.Suppress('"')) +
      _MESSAGE + pyparsing.Optional(pyparsing.Suppress('"')) +
      pyparsing.Suppress('[**]') +
      pyparsing.Optional(
          pyparsing.Suppress(pyparsing.Literal('[Classification:')) +
          pyparsing.Regex('[^]]*').setResultsName('classification') +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(
          pyparsing.Suppress('[Priority:') +
          text_parser.PyparsingConstants.INTEGER.setResultsName('priority') +
          pyparsing.Suppress(']')) +
      pyparsing.Suppress('{') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('protocol') +
      pyparsing.Suppress('}') +
      _IP_ADDRESS.setResultsName('source_ip_address') +
      pyparsing.Optional(
          pyparsing.Suppress(':') +
          text_parser.PyparsingConstants.INTEGER.setResultsName(
              'source_port')) +
      pyparsing.Suppress('->') +
      _IP_ADDRESS.setResultsName('destination_ip_address') +
      pyparsing.Optional(
          pyparsing.Suppress(':') +
          text_parser.PyparsingConstants.INTEGER.setResultsName(
              'destination_port')) +
      pyparsing.Suppress(pyparsing.lineEnd()))

  _LINE_STRUCTURES = [('fastlog_line', _FASTLOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
        microseconds (int): fraction of second in microseconds.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    month = self._GetValueFromStructure(structure, 'month')
    year = self._GetValueFromStructure(structure, 'year')
    day_of_month = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')
    microseconds = self._GetValueFromStructure(structure, 'microseconds')

    if year:
      year += 2000
    else:
      self._UpdateYear(month)

      year = self._GetYear()

    return year, month, day_of_month, hours, minutes, seconds, microseconds

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

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

    try:
      time_elements_tuple = self._GetTimeElementsTuple(structure)
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      return

    event_data = SnortFastAlertEventData()
    event_data.rule_identifier = self._GetValueFromStructure(
        structure, 'rule_identifier')
    event_data.message = str(
        self._GetValueFromStructure(structure, 'message')).strip()
    event_data.priority = self._GetValueFromStructure(structure, 'priority')
    event_data.classification = self._GetValueFromStructure(
        structure, 'classification')
    event_data.protocol = self._GetValueFromStructure(structure, 'protocol')
    event_data.source_ip = self._GetValueFromStructure(
        structure, 'source_ip_address')
    event_data.source_port = self._GetValueFromStructure(
        structure, 'source_port')
    event_data.destination_ip = self._GetValueFromStructure(
        structure, 'destination_ip_address')
    event_data.destination_port = self._GetValueFromStructure(
        structure, 'destination_port')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

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

    self._SetEstimatedYear(parser_mediator)

    return bool(self._VERIFICATION_REGEX.match(line))


text_parser.SingleLineTextParser.RegisterPlugin(SnortFastLogTextPlugin)
