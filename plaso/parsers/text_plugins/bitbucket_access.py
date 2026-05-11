"""Text parser plugin for Atlassian Bitbucket access log files.

This is for the atlassian-bitbucket-access.log file, one of multiple log
files produced by a Bitbucket DC/Server installation.

The standard HTTP/SSH access log format is pipe-delimited:
  ip_address | protocol | request_identifier | user | timestamp | "request" |
  "referer" "user-agent" | status | bytes_read | bytes_written | labels |
  request_time | session_identifier |

The Mesh/gRPC access log format has two additional fields:
  ip_address | grpc | request_identifier | mesh_execution_identifier | user |
  timestamp | "action" | - | status | bytes_read | bytes_written | mesh_in |
  mesh_out | duration_ns | labels | session_identifier |

Also see:
  https://support.atlassian.com/bitbucket-data-center/kb/how-to-read-the-bitbucket-data-center-log-formats/
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class BitbucketAccessEventData(events.EventData):
  """Bitbucket access log event data.

  Attributes:
    http_request_method (str): HTTP request method (GET, POST, etc.), or
        'SSH' for SSH requests, or None for gRPC/Mesh action lines.
    http_request_uri (str): HTTP request URI, SSH command, or gRPC action.
    http_request_user_agent (str): HTTP request user agent, or None for
        SSH/gRPC requests.
    http_response_bytes_read (int): number of bytes read from the client.
    http_response_bytes_written (int): number of bytes written to the client.
    http_response_code (int): HTTP response status code.
    http_version (str): HTTP request version, or None for SSH/gRPC requests.
    labels (str): request classification labels, such as push, fetch, clone,
        access-token:id:..., async, protocol:2 or refs.
    mesh_execution_identifier (str): Mesh execution identifier, only present for
        gRPC/Mesh log lines.
    protocol (str): protocol used, such as http, https, ssh or grpc.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    remote_address (str): remote IP address(es), including X-Forwarded-For
        proxies. Multiple addresses are comma-separated.
    request_identifier (str): unique request identifier, correlatable with audit
        log.
    request_time (int): time taken to process the request in milliseconds
        (HTTP/SSH) or nanoseconds (gRPC/Mesh), or None if not available.
    session_identifier (str): session identifier.
    ssh_repository_path (str): SSH repository path for SSH requests, or None.
    user_name (str): the name of the authenticated user.
  """

  DATA_TYPE = 'atlassian:bitbucket:access'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.http_request_method = None
    self.http_request_uri = None
    self.http_request_user_agent = None
    self.http_response_bytes_read = None
    self.http_response_bytes_written = None
    self.http_response_code = None
    self.http_version = None
    self.labels = None
    self.mesh_execution_identifier = None
    self.protocol = None
    self.recorded_time = None
    self.remote_address = None
    self.request_identifier = None
    self.request_time = None
    self.session_identifier = None
    self.ssh_repository_path = None
    self.user_name = None


class BitbucketAccessTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Bitbucket access log files."""

  NAME = 'bitbucket_access'
  DATA_FORMAT = (
      'Atlassian Bitbucket access log (atlassian-bitbucket-access.log) file')

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  # Pipe as field separator.
  _SEPARATOR = pyparsing.Suppress(pyparsing.Literal('|'))

  # Integer or dash (used for optional numeric fields).
  _INT_OR_DASH = pyparsing.Literal('-') | _INTEGER

  # Remote address: IPv4, IPv6, or comma-separated list of addresses.
  _REMOTE_ADDRESS = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphanums + '.:,')).set_results_name(
          'remote_address')

  # Request ID: alphanumeric token with @/* prefix and x separators, or '-'.
  _REQUEST_ID = (
      pyparsing.Word(pyparsing.alphanums + '@*-_x') |
      pyparsing.Literal('-'))

  # User name: alphanumeric with common separators, or '-'.
  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-_./') |
      pyparsing.Literal('-'))

  # Session ID: short alphanumeric token or '-'.
  _SESSION_ID = (
      pyparsing.Word(pyparsing.alphanums + '-_') |
      pyparsing.Literal('-'))

  # Date and time format: 2020-09-08 07:53:45,084
  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(',') + _THREE_DIGITS).set_results_name('date_time')

  # HTTP request methods.
  _HTTP_METHODS = [
      'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT',
      'TRACE']

  # Request URI characters.
  _REQUEST_URI = pyparsing.Word(pyparsing.alphanums + '/-_.?=%&:+<>#~[]@!,()')

  # HTTP request: "METHOD /uri HTTP/1.1"
  _HTTP_REQUEST = pyparsing.Group(
      pyparsing.Suppress('"') +
      pyparsing.one_of(_HTTP_METHODS).set_results_name('http_method') +
      _REQUEST_URI.copy().set_results_name('request_url') +
      pyparsing.Word(pyparsing.alphanums + '/.').set_results_name(
          'http_version') +
      pyparsing.Suppress('"')).set_results_name('http_request')

  # SSH request: "SSH - git-upload-pack '/repo.git'"
  _SSH_REQUEST = pyparsing.Group(
      pyparsing.Suppress('"') +
      pyparsing.Literal('SSH').set_results_name('http_method') +
      pyparsing.Suppress(pyparsing.Literal('-')) +
      pyparsing.Word(pyparsing.alphanums + '-_').set_results_name(
          'request_url') +
      pyparsing.QuotedString("'").set_results_name('ssh_repo') +
      pyparsing.Suppress('"')).set_results_name('http_request')

  # gRPC action: "ServiceName/MethodName"
  _GRPC_REQUEST = pyparsing.Group(
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').set_results_name('request_url') +
      pyparsing.Suppress('"')).set_results_name('http_request')

  # Referer and user agent fields: "" "user-agent-string"
  _REFERER = (
      pyparsing.Suppress('"') +
      pyparsing.Optional(pyparsing.Word(
          pyparsing.alphanums + '/-_.?=%&:+<>#~[]@!,()')).set_results_name(
              'referer') +
      pyparsing.Suppress('"'))

  _USER_AGENT = (
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').set_results_name('user_agent') +
      pyparsing.Suppress('"'))

  # Labels field: arbitrary text up to the next pipe separator.
  _LABELS = pyparsing.SkipTo(pyparsing.Literal('|')).set_results_name('labels')

  # HTTP/SSH access log line:
  # ip_address | protocol | request_identifier | user | timestamp | "request" |
  # "referer" "user-agent" | status | bytes_read | bytes_written | labels |
  # request_time | session_identifier |
  _HTTP_ACCESS_LOG_LINE = (
      _REMOTE_ADDRESS + _SEPARATOR +
      pyparsing.Word(pyparsing.alphanums).set_results_name('protocol') +
      _SEPARATOR +
      _REQUEST_ID.copy().set_results_name('request_identifier') + _SEPARATOR +
      _USER_NAME.copy().set_results_name('user_name') + _SEPARATOR +
      _DATE_TIME + _SEPARATOR +
      (_HTTP_REQUEST | _SSH_REQUEST | _GRPC_REQUEST.copy()) +
      _SEPARATOR +
      _REFERER + _USER_AGENT + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('status_code') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('bytes_read') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('bytes_written') + _SEPARATOR +
      _LABELS + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('request_time') + _SEPARATOR +
      _SESSION_ID.copy().set_results_name('session_identifier') + _SEPARATOR +
      pyparsing.Suppress(pyparsing.LineEnd()))

  # gRPC/Mesh access log line:
  # ip_address | grpc | request_identifier | mesh_execution_identifier | user |
  # timestamp | "action" | - | status | bytes_read | bytes_written | mesh_in |
  # mesh_out | duration_ns | session_identifier |
  _GRPC_ACCESS_LOG_LINE = (
      _REMOTE_ADDRESS.copy() + _SEPARATOR +
      pyparsing.Literal('grpc').set_results_name('protocol') + _SEPARATOR +
      _REQUEST_ID.copy().set_results_name('request_identifier') + _SEPARATOR +
      (pyparsing.Word(pyparsing.alphanums + '@*-_x') |
       pyparsing.Literal('-')).set_results_name('mesh_execution_identifier') +
      _SEPARATOR +
      _USER_NAME.copy().set_results_name('user_name') + _SEPARATOR +
      _DATE_TIME.copy() + _SEPARATOR +
      _GRPC_REQUEST.copy() + _SEPARATOR +
      pyparsing.Suppress(pyparsing.Literal('-')) + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('status_code') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('bytes_read') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('bytes_written') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('mesh_in') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('mesh_out') + _SEPARATOR +
      _INT_OR_DASH.copy().set_results_name('duration_ns') + _SEPARATOR +
      _SESSION_ID.copy().set_results_name('session_identifier') + _SEPARATOR +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _LINE_STRUCTURES = [
      ('grpc_access_log', _GRPC_ACCESS_LOG_LINE),
      ('http_access_log', _HTTP_ACCESS_LOG_LINE)]

  VERIFICATION_GRAMMAR = _GRPC_ACCESS_LOG_LINE | _HTTP_ACCESS_LOG_LINE

  VERIFICATION_LITERALS = [
      ' | grpc | ', ' | http | ', ' | https | ', ' | ssh | ']

  def _GetStrippedValue(self, structure, name, default_value=None):
    """Retrieves a token value from a Pyparsing structure and strips '' or '-'.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.
      default_value (Optional[object]): default value.

    Returns:
      object: value in the token or default value if the token is not available
          in the structure.
    """
    value = self._GetValueFromStructure(structure, name)
    if value in (None, '', '-'):
      return default_value

    return value

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
    if key not in ('http_access_log', 'grpc_access_log'):
      raise errors.ParseError(
          f'Unable to parse record, unknown structure: {key:s}')

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    http_request = self._GetValueFromStructure(structure, 'http_request')

    labels = self._GetValueFromStructure(
        structure, 'labels', default_value='').strip()

    event_data = BitbucketAccessEventData()
    event_data.http_response_bytes_read = self._GetStrippedValue(
        structure, 'bytes_read')
    event_data.http_response_bytes_written = self._GetStrippedValue(
        structure, 'bytes_written')
    event_data.http_response_code = self._GetStrippedValue(
        structure, 'status_code')
    event_data.http_request_user_agent = (
        self._GetStringValueFromStructure(structure, 'user_agent') or None)
    event_data.labels = None if not labels or labels == '-' else labels
    event_data.mesh_execution_identifier = self._GetStrippedValue(
        structure, 'mesh_execution_identifier')
    event_data.protocol = self._GetValueFromStructure(structure, 'protocol')
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
    event_data.remote_address = self._GetValueFromStructure(
        structure, 'remote_address')
    event_data.request_identifier = self._GetStrippedValue(
        structure, 'request_identifier')
    event_data.request_time = self._GetStrippedValue(structure, 'request_time')
    event_data.session_identifier = self._GetStrippedValue(
        structure, 'session_identifier')
    event_data.user_name = self._GetStrippedValue(structure, 'user_name')

    if http_request:
      event_data.http_request_method = self._GetValueFromStructure(
          http_request, 'http_method')
      event_data.http_request_uri = self._GetValueFromStructure(
          http_request, 'request_url')
      event_data.http_version = self._GetValueFromStructure(
          http_request, 'http_version') or None
      event_data.ssh_repository_path = self._GetValueFromStructure(
          http_request, 'ssh_repo') or None

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived.
    """
    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_structure)

      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(BitbucketAccessTextPlugin)
