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


class SnortFastLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Snort3/Suricata fast-log alert log files."""

  NAME = 'snort:fastlog:alert'
  DATA_FORMAT = 'Snort3/Suricata fast-log alert log (fast.log) file'

  _VERIFICATION_REGEX = re.compile(
      # Date regex
      r'^(\d{2}\/)?\d{2}\/\d{2}\-\d{2}:\d{2}:\d{2}.\d{6}\s*'
      # Separator ([**])
      r'\[\*\*\]\s*'
      # Rule identifier
      r'\[\d*:\d*:\d*\]\s*'
      # Message
      r'"?.*\"?\s*\[\*\*\]\s*'
      # Optional Classification
      r'(\[Classification:\s.*\])?\s*'
      # Optional Priority
      r'(\[Priority\:\s*\d{1}\])?\s*'
      # Procotol
      r'\{\w+\}\s*'
      # Source IPv6 address
      r'((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:'
      r'|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}'
      r'(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[ 0-9a-fA-F]{1,4})'
      r'{1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4} |([0-9a-fA-F]'
      r'{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((: [0-9a-fA-F]'
      r'{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4})'
      r'{0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2 [0-4]'
      r'|1{0,1}[0-9]){0,1}[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}'
      r'[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}'
      r'[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
      # Source IPv4 address
      r'|(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?'
      r'[0-9][0-9]?)\.(25[0-5] |2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|'
      r'2[0-4][0-9]|[01]?[0-9][0-9]?))'
      # Optional source port
      r'(:\d*)?\s*'
      # Separator '->'
      r'\-\>\s*'
      # Destination IPv6-address
      r'((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:'
      r'|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}'
      r'(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[ 0-9a-fA-F]{1,4})'
      r'{1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4} |([0-9a-fA-F]'
      r'{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((: [0-9a-fA-F]'
      r'{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4})'
      r'{0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2 [0-4]'
      r'|1{0,1}[0-9]){0,1}[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}'
      r'[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}'
      r'[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
      # Destination IPv4 address
      r'|(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?'
      r'[0-9][0-9]?)\.(25[0-5] |2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|'
      r'2[0-4][0-9]|[01]?[0-9][0-9]?))'
      # Optional destination port
      r'(:\d*)?$')

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      text_parser.PyParseIntCast)

  _DATE_MONTH_DAY = (
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('month') +
      pyparsing.Suppress('/') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('day_of_month'))

  _DATE_YEAR_MONTH_DAY = (
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('year') +
      pyparsing.Suppress('/') + _DATE_MONTH_DAY)

  _DATE_TIME = (
      (_DATE_YEAR_MONTH_DAY | _DATE_MONTH_DAY) +
      pyparsing.Suppress(text_parser.PyparsingConstants.HYPHEN) +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('hours') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('minutes') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('seconds') +
      pyparsing.Suppress('.') +
      _SIX_DIGITS.setResultsName('fraction_of_second'))

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
      text_parser.PyparsingConstants.IP_ADDRESS.setResultsName('src_ip') +
      pyparsing.Optional(
          pyparsing.Suppress(':') +
          text_parser.PyparsingConstants.INTEGER.setResultsName('src_port')) +
      pyparsing.Suppress('->') +
      text_parser.PyparsingConstants.IP_ADDRESS.setResultsName('dst_ip') +
      pyparsing.Optional(
          pyparsing.Suppress(':') +
          text_parser.PyparsingConstants.INTEGER.setResultsName('dst_port')) +
      pyparsing.Suppress(pyparsing.lineEnd()))

  _LINE_STRUCTURES = [('fastlog_line', _FASTLOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser."""
    super(SnortFastLogTextPlugin, self).__init__()
    self._last_month = 0
    self._year_use = 0

  def _UpdateYear(self, parser_mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      month (int): month observed by the parser, where January is 1.
    """
    if not self._year_use:
      self._year_use = parser_mediator.GetEstimatedYear()

    if not self._last_month:
      self._last_month = month
      return

    if self._last_month == 12 and month == 1:
      self._year_use += 1
    self._last_month = month

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

    month = self._GetValueFromStructure(structure, 'month')
    year = self._GetValueFromStructure(structure, 'year')
    day_of_month = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')
    fraction_of_second = self._GetValueFromStructure(
        structure, 'fraction_of_second')

    if month != 0:
      self._UpdateYear(parser_mediator, month)

    if year is not None:
      year += 2000
    else:
      year = self._year_use

    time_elements_tuple = (
        year, month, day_of_month, hours, minutes, seconds, fraction_of_second)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True

    except (ValueError, TypeError):
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
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
    event_data.source_ip = self._GetValueFromStructure(structure, 'src_ip')
    event_data.source_port = self._GetValueFromStructure( structure, 'src_port')
    event_data.destination_ip = self._GetValueFromStructure(structure, 'dst_ip')
    event_data.destination_port = self._GetValueFromStructure(
        structure, 'dst_port')

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

    self._last_month = 0
    self._year_use = 0

    return bool(self._VERIFICATION_REGEX.match(line))


text_parser.PyparsingSingleLineTextParser.RegisterPlugin(SnortFastLogTextPlugin)
