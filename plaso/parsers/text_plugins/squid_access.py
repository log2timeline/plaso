# -*- coding: utf-8 -*-
"""Text parser plugin for Squid Proxy access log files.

Parser based on the Squid access log format defined in:
https://wiki.squid-cache.org/Features/LogFormat
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SquidAccessLogEventData(events.EventData):
  """Squid access log event data.

  Attributes:
    bytes_transferred (int): number of bytes transferred.
    client_ip (str): client IP address (IPv4 or IPv6).
    content_type (str): content type or MIME type.
    hierarchy_info (str): hierarchy code and peer information.
    http_request (str): HTTP request method and URL.
    http_status (int): HTTP status code.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    response_time (int): response time in milliseconds.
    result_code (str): Squid result code (e.g., TCP_TUNNEL, TCP_MISS).
    user_id (str): authenticated user identifier.
  """

  DATA_TYPE = 'squid:access_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(SquidAccessLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.bytes_transferred = None
    self.client_ip = None
    self.content_type = None
    self.hierarchy_info = None
    self.http_request = None
    self.http_status = None
    self.recorded_time = None
    self.response_time = None
    self.result_code = None
    self.user_id = None


class SquidAccessLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Squid Proxy access log files."""

  NAME = 'squid_access'
  DATA_FORMAT = 'Squid proxy access log file'

  _INTEGER = pyparsing.Word(pyparsing.nums).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  # Unix timestamp with milliseconds (e.g., 1677971734.079)
  _TIMESTAMP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums) +
      pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums)).set_parse_action(
          lambda tokens: float(tokens[0]))

  # IP address (IPv4 or IPv6)
  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address)

  # HTTP methods
  _HTTP_METHOD = pyparsing.one_of([
      'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT',
      'TRACE'])

  # Result code with HTTP status (e.g., TCP_TUNNEL/200)
  _RESULT_CODE = pyparsing.Word(pyparsing.alphas + '_')
  _HTTP_STATUS = pyparsing.Word(pyparsing.nums)
  _RESULT_WITH_STATUS = pyparsing.Combine(
      _RESULT_CODE + pyparsing.Literal('/') + _HTTP_STATUS)

  # Request (method and URL)
  _REQUEST = pyparsing.Combine(
      _HTTP_METHOD + pyparsing.Literal(' ') +
      pyparsing.Word(pyparsing.printables, exclude_chars=' '))

  # User identifier or dash
  _USER_OR_DASH = (
      pyparsing.Word(pyparsing.alphanums + '@' + '.' + '-' + '_') |
      pyparsing.Literal('-'))

  # Hierarchy information (e.g., HIER_DIRECT/1.2.3.4)
  _HIERARCHY = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphas + '_') +
      pyparsing.Literal('/') +
      (_IP_ADDRESS | pyparsing.Literal('-')))

  # Content type or dash
  _CONTENT_TYPE = (
      pyparsing.Word(pyparsing.alphanums + '/' + '-' + '+' + '.') |
      pyparsing.Literal('-'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Squid access log format:
  # timestamp response_time client_ip result_code/status bytes request user
  # hierarchy content_type
  _LOG_LINE = (
      _TIMESTAMP.set_results_name('timestamp') +
      _INTEGER.set_results_name('response_time') +
      _IP_ADDRESS.set_results_name('client_ip') +
      _RESULT_WITH_STATUS.set_results_name('result_with_status') +
      _INTEGER.set_results_name('bytes') +
      _REQUEST.set_results_name('request') +
      _USER_OR_DASH.set_results_name('user') +
      _HIERARCHY.set_results_name('hierarchy') +
      _CONTENT_TYPE.set_results_name('content_type') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

  VERIFICATION_LITERALS = [
      'CONNECT ', 'DELETE ', 'GET ', 'HEAD ', 'OPTIONS ',
      'PATCH ', 'POST ', 'PUT ', 'TRACE ']

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
    timestamp = self._GetValueFromStructure(structure, 'timestamp')
    result_with_status = self._GetValueFromStructure(
        structure, 'result_with_status')
    user = self._GetValueFromStructure(structure, 'user')
    content_type = self._GetValueFromStructure(structure, 'content_type')

    # Parse result code and HTTP status from combined field
    if result_with_status:
      parts = result_with_status.split('/')
      result_code = parts[0] if len(parts) > 0 else None
      http_status = int(parts[1]) if len(parts) > 1 else None
    else:
      result_code = None
      http_status = None

    # Convert dash to None for optional fields
    if user == '-':
      user = None
    if content_type == '-':
      content_type = None

    event_data = SquidAccessLogEventData()
    event_data.bytes_transferred = self._GetValueFromStructure(
        structure, 'bytes')
    event_data.client_ip = self._GetValueFromStructure(structure, 'client_ip')
    event_data.content_type = content_type
    event_data.hierarchy_info = self._GetValueFromStructure(
        structure, 'hierarchy')
    event_data.http_request = self._GetValueFromStructure(structure, 'request')
    event_data.http_status = http_status
    event_data.recorded_time = self._ParseTimestamp(timestamp)
    event_data.response_time = self._GetValueFromStructure(
        structure, 'response_time')
    event_data.result_code = result_code
    event_data.user_id = user

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimestamp(self, timestamp):
    """Parses a Unix timestamp with milliseconds.

    Args:
      timestamp (float): Unix timestamp with milliseconds.

    Returns:
      dfdatetime.PosixTimeInMicroseconds: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the timestamp.
    """
    try:
      # Convert timestamp to microseconds
      timestamp_microseconds = int(timestamp * 1000000)
      return dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp_microseconds)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse timestamp with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct plugin, False otherwise.
    """
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    timestamp = self._GetValueFromStructure(structure, 'timestamp')

    try:
      self._ParseTimestamp(timestamp)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(SquidAccessLogTextPlugin)
