# -*- coding: utf-8 -*-
"""Text parser plugin for Apache access log (access.log) files.

Parser based on the two default apache formats, common and combined log format
defined in https://httpd.apache.org/docs/2.4/logs.html
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class ApacheAccessLogEventData(events.EventData):
  """Apache access log event data.

  Attributes:
    http_request_referer (str): http request referer header information.
    http_request (str): first line of http request.
    http_request_user_agent (str): http request user agent header information.
    http_response_bytes (int): http response bytes size without headers.
    http_response_code (int): http response code from server.
    ip_address (str): IPv4 or IPv6 addresses.
    port_number (int): canonical port of the server serving the request.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    remote_name (str): remote logname (from identd, if supplied).
    server_name (str): canonical hostname of the server serving the request.
    user_name (str): logged user name.
  """

  DATA_TYPE = 'apache:access_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(ApacheAccessLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.http_request = None
    self.http_request_referer = None
    self.http_request_user_agent = None
    self.http_response_bytes = None
    self.http_response_code = None
    self.ip_address = None
    self.port_number = None
    self.recorded_time = None
    self.remote_name = None
    self.server_name = None
    self.user_name = None


class ApacheAccessLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Apache access log (access.log) files."""

  NAME = 'apache_access'
  DATA_FORMAT = 'Apache access log (access.log) file'

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  _TIME_ZONE_OFFSET = (
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  # Date and time values are formatted as: [18/Sep/2011:19:18:28 -0400]
  _DATE_TIME = pyparsing.Group(
      pyparsing.Suppress('[') + _TWO_DIGITS +
      pyparsing.Suppress('/') + _THREE_LETTERS +
      pyparsing.Suppress('/') + _FOUR_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      _TIME_ZONE_OFFSET + pyparsing.Suppress(']')).setResultsName('date_time')

  _HTTP_METHOD = pyparsing.oneOf([
      'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT',
      'TRACE'])

  _HTTP_VERSION = pyparsing.Combine(
      pyparsing.Literal('HTTP/') + pyparsing.Word(pyparsing.nums + '.'))

  _HTTP_REQUEST = pyparsing.Suppress('"') + pyparsing.Group(
      _HTTP_METHOD + pyparsing.Regex(r'\S*') + _HTTP_VERSION).setResultsName(
          'http_request') + pyparsing.Suppress('"')

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address)

  _REMOTE_NAME = (
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Literal('-')).setResultsName('remote_name')

  _RESPONSE_BYTES = (
      pyparsing.Literal('-') | _INTEGER).setResultsName('response_bytes')

  _SERVER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-' + '.').setResultsName(
          'server_name'))

  _USER_AGENT = (
      pyparsing.Suppress('"') +
      pyparsing.CharsNotIn('"').setResultsName('user_agent') +
      pyparsing.Suppress('"'))

  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '@' + pyparsing.alphanums + '.') |
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Literal('-')).setResultsName('user_name')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b"
  _COMMON_LOG_FORMAT_LINE = (
      _IP_ADDRESS.setResultsName('ip_address') +
      _REMOTE_NAME +
      _USER_NAME +
      _DATE_TIME +
      _HTTP_REQUEST +
      _INTEGER.setResultsName('response_code') +
      _RESPONSE_BYTES +
      _END_OF_LINE)

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
  _COMBINED_LOG_FORMAT_LINE = (
      _IP_ADDRESS.setResultsName('ip_address') +
      _REMOTE_NAME +
      _USER_NAME +
      _DATE_TIME +
      _HTTP_REQUEST +
      _INTEGER.setResultsName('response_code') +
      _RESPONSE_BYTES +
      pyparsing.QuotedString('"').setResultsName('referer') +
      _USER_AGENT +
      _END_OF_LINE)

  # "vhost_combined" format as used by Debian and related distributions.
  # "%v:%p %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
  _VHOST_COMBINED_LOG_FORMAT_LINE = (
      _SERVER_NAME +
      pyparsing.Suppress(':') +
      _INTEGER.setResultsName('port_number') +
      _IP_ADDRESS.setResultsName('ip_address') +
      _REMOTE_NAME +
      _USER_NAME +
      _DATE_TIME +
      _HTTP_REQUEST +
      _INTEGER.setResultsName('response_code') +
      _RESPONSE_BYTES +
      pyparsing.QuotedString('"').setResultsName('referer') +
      _USER_AGENT +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('combined_log_format', _COMBINED_LOG_FORMAT_LINE),
      ('common_log_format', _COMMON_LOG_FORMAT_LINE),
      ('vhost_combined_log_format', _VHOST_COMBINED_LOG_FORMAT_LINE)]

  VERIFICATION_GRAMMAR = (
      _COMBINED_LOG_FORMAT_LINE ^ _COMMON_LOG_FORMAT_LINE ^
      _VHOST_COMBINED_LOG_FORMAT_LINE)

  VERIFICATION_LITERALS = [
      '"CONNECT ', '"DELETE ', '"GET ', '"HEAD ', ' HTTP/', '"OPTIONS ',
      '"PATCH ', '"POST ', '"PUT ', '"TRACE ']

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
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    http_request = self._GetValueFromStructure(structure, 'http_request')
    if http_request:
      http_request = ' '.join(http_request)

    remote_name = self._GetValueFromStructure(structure, 'remote_name')
    if remote_name == '-':
      remote_name = None

    user_name = self._GetValueFromStructure(structure, 'user_name')
    if user_name == '-':
      user_name = None

    event_data = ApacheAccessLogEventData()
    event_data.http_request = http_request
    event_data.http_response_bytes = self._GetValueFromStructure(
        structure, 'response_bytes')
    event_data.http_response_code = self._GetValueFromStructure(
        structure, 'response_code')
    event_data.ip_address = self._GetValueFromStructure(structure, 'ip_address')
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
    event_data.remote_name = remote_name
    event_data.user_name = user_name

    if key in ('combined_log_format', 'vhost_combined_log_format'):
      referer = self._GetValueFromStructure(structure, 'referer')
      if referer == '-':
        referer = None

      event_data.http_request_referer = referer
      event_data.http_request_user_agent = self._GetValueFromStructure(
          structure, 'user_agent')

    if key == 'vhost_combined_log_format':
      event_data.port_number = self._GetValueFromStructure(
          structure, 'port_number')
      event_data.server_name = self._GetValueFromStructure(
          structure, 'server_name')

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
      (day_of_month, month_string, year, hours, minutes, seconds,
       time_zone_sign, time_zone_hours, time_zone_minutes) = (
          time_elements_structure)

      month = self._MONTH_DICT.get(month_string.lower(), 0)

      time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
      if time_zone_sign == '-':
        time_zone_offset *= -1

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)
      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=time_zone_offset)

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
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(ApacheAccessLogTextPlugin)
