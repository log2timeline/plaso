"""Text parser plugin for Atlassian Bitbucket access log files.

This is for the atlassian-bitbucket-access.log file, one of multiple log
files produced by a Bitbucket DC/Server installation.

The standard HTTP/SSH access log format is pipe-delimited:
  ip | protocol | request_id | user | timestamp | "request" |
  "referer" "user-agent" | status | bytes_read | bytes_written |
  labels | request_time | session_id |

The Mesh/gRPC access log format has two additional fields:
  ip | grpc | request_id | mesh_execution_id | user | timestamp |
  "action" | - | status | bytes_read | bytes_written | mesh_in | mesh_out |
  duration_ns | labels | session_id |

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
    labels (str): request classification labels (e.g. push, fetch, clone,
        access-token:id:..., async, protocol:2, refs).
    mesh_execution_id (str): Mesh execution identifier, only present for
        gRPC/Mesh log lines.
    protocol (str): protocol used (e.g. http, https, ssh, grpc).
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    remote_address (str): remote IP address(es), including X-Forwarded-For
        proxies. Multiple addresses are comma-separated.
    request_id (str): unique request identifier, correlatable with audit log.
    request_time (int): time taken to process the request in milliseconds
        (HTTP/SSH) or nanoseconds (gRPC/Mesh), or None if not available.
    session_id (str): session identifier.
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
    self.mesh_execution_id = None
    self.protocol = None
    self.recorded_time = None
    self.remote_address = None
    self.request_id = None
    self.request_time = None
    self.session_id = None
    self.ssh_repository_path = None
    self.user_name = None


def _MakeSep():
  """Returns a fresh pipe separator suppressor."""
  return pyparsing.Suppress(pyparsing.Literal('|'))


def _MakeInt():
  """Returns a fresh integer parser."""
  return pyparsing.Word(pyparsing.nums).set_parse_action(
      lambda tokens: int(tokens[0], 10))


def _MakeIntOrDash():
  """Returns a fresh integer-or-dash parser."""
  return pyparsing.Literal('-') | _MakeInt()


def _MakeTwoDigits():
  """Returns a fresh two-digit integer parser."""
  return pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))


def _MakeThreeDigits():
  """Returns a fresh three-digit integer parser."""
  return pyparsing.Word(pyparsing.nums, exact=3).set_parse_action(
      lambda tokens: int(tokens[0], 10))


def _MakeFourDigits():
  """Returns a fresh four-digit integer parser."""
  return pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))


def _MakeDateTime():
  """Returns a fresh date-time parser for format: YYYY-MM-DD HH:MM:SS,mmm."""
  return (
      _MakeFourDigits() + pyparsing.Suppress('-') +
      _MakeTwoDigits() + pyparsing.Suppress('-') +
      _MakeTwoDigits() + _MakeTwoDigits() +
      pyparsing.Suppress(':') + _MakeTwoDigits() +
      pyparsing.Suppress(':') + _MakeTwoDigits() +
      pyparsing.Suppress(',') + _MakeThreeDigits()
  ).set_results_name('date_time')


def _MakeRemoteAddress():
  """Returns a fresh remote address parser."""
  return pyparsing.Combine(
      pyparsing.Word(pyparsing.alphanums + '.:,')
  ).set_results_name('remote_address')


def _MakeRequestId():
  """Returns a fresh request ID parser."""
  return (
      pyparsing.Word(pyparsing.alphanums + '@*-_x') |
      pyparsing.Literal('-')).set_results_name('request_id')


def _MakeUserName():
  """Returns a fresh user name parser."""
  return (
      pyparsing.Word(pyparsing.alphanums + '-_./') |
      pyparsing.Literal('-')).set_results_name('user_name')


def _MakeSessionId():
  """Returns a fresh session ID parser."""
  return (
      pyparsing.Word(pyparsing.alphanums + '-_') |
      pyparsing.Literal('-')).set_results_name('session_id')


def _MakeLabels():
  """Returns a fresh labels parser."""
  return pyparsing.SkipTo(
      pyparsing.Literal('|')).set_results_name('labels')


_HTTP_METHODS = [
    'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT',
    'TRACE']

_REQUEST_URI = pyparsing.Word(pyparsing.alphanums + '/-_.?=%&:+<>#~[]@!,()')


def _MakeHttpRequest():
  """Returns a fresh HTTP request parser."""
  return pyparsing.Group(
      pyparsing.Suppress('"') +
      pyparsing.one_of(_HTTP_METHODS).set_results_name('http_method') +
      _REQUEST_URI.copy().set_results_name('request_url') +
      pyparsing.Word(pyparsing.alphanums + '/.').set_results_name(
          'http_version') +
      pyparsing.Suppress('"')).set_results_name('http_request')


def _MakeSshRequest():
  """Returns a fresh SSH request parser."""
  return pyparsing.Group(
      pyparsing.Suppress('"') +
      pyparsing.Literal('SSH').set_results_name('http_method') +
      pyparsing.Suppress(pyparsing.Literal('-')) +
      pyparsing.Word(pyparsing.alphanums + '-_').set_results_name(
          'request_url') +
      pyparsing.QuotedString("'").set_results_name('ssh_repo') +
      pyparsing.Suppress('"')).set_results_name('http_request')


def _MakeGrpcRequest():
  """Returns a fresh gRPC action parser."""
  return pyparsing.Group(
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').set_results_name('request_url') +
      pyparsing.Suppress('"')).set_results_name('http_request')


def _MakeRefererUserAgent():
  """Returns a fresh referer + user-agent parser."""
  referer = (
      pyparsing.Suppress('"') +
      pyparsing.Optional(
          pyparsing.Word(pyparsing.alphanums + '/-_.?=%&:+<>#~[]@!,()')
      ).set_results_name('referer') +
      pyparsing.Suppress('"'))
  user_agent = (
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').set_results_name('user_agent') +
      pyparsing.Suppress('"'))
  return referer + user_agent


def _MakeHttpAccessLogLine():
  """Returns a fresh HTTP/SSH access log line grammar."""
  return (
      _MakeRemoteAddress() + _MakeSep() +
      pyparsing.Word(pyparsing.alphanums).set_results_name('protocol') +
      _MakeSep() +
      _MakeRequestId() + _MakeSep() +
      _MakeUserName() + _MakeSep() +
      _MakeDateTime() + _MakeSep() +
      (_MakeHttpRequest() | _MakeSshRequest() | _MakeGrpcRequest()) +
      _MakeSep() +
      _MakeRefererUserAgent() + _MakeSep() +
      _MakeIntOrDash().set_results_name('status_code') + _MakeSep() +
      _MakeIntOrDash().set_results_name('bytes_read') + _MakeSep() +
      _MakeIntOrDash().set_results_name('bytes_written') + _MakeSep() +
      _MakeLabels() + _MakeSep() +
      _MakeIntOrDash().set_results_name('request_time') + _MakeSep() +
      _MakeSessionId() + _MakeSep() +
      pyparsing.Suppress(pyparsing.LineEnd()))


def _MakeGrpcAccessLogLine():
  """Returns a fresh gRPC/Mesh access log line grammar.

  The gRPC/Mesh access log has 15 pipe-separated fields:
  ip | grpc | request_id | mesh_execution_id | user | timestamp |
  "action" | - | status | bytes_read | bytes_written |
  mesh_in | mesh_out | duration_ns | session_id |
  """
  return (
      _MakeRemoteAddress() + _MakeSep() +
      pyparsing.Literal('grpc').set_results_name('protocol') + _MakeSep() +
      _MakeRequestId() + _MakeSep() +
      (pyparsing.Word(pyparsing.alphanums + '@*-_x') |
       pyparsing.Literal('-')).set_results_name('mesh_execution_id') +
      _MakeSep() +
      _MakeUserName() + _MakeSep() +
      _MakeDateTime() + _MakeSep() +
      _MakeGrpcRequest() + _MakeSep() +
      pyparsing.Suppress(pyparsing.Literal('-')) + _MakeSep() +
      _MakeIntOrDash().set_results_name('status_code') + _MakeSep() +
      _MakeIntOrDash().set_results_name('bytes_read') + _MakeSep() +
      _MakeIntOrDash().set_results_name('bytes_written') + _MakeSep() +
      _MakeIntOrDash().set_results_name('mesh_in') + _MakeSep() +
      _MakeIntOrDash().set_results_name('mesh_out') + _MakeSep() +
      _MakeIntOrDash().set_results_name('duration_ns') + _MakeSep() +
      _MakeSessionId() + _MakeSep() +
      pyparsing.Suppress(pyparsing.LineEnd()))


class BitbucketAccessTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Bitbucket access log files."""

  NAME = 'bitbucket_access'
  DATA_FORMAT = (
      'Atlassian Bitbucket access log (atlassian-bitbucket-access.log) file')

  ENCODING = 'utf-8'

  # Build completely independent grammar instances for each line structure
  # to avoid pyparsing result name mutation when shared objects are used in
  # multiple grammar expressions combined with ^ (Or).
  _HTTP_ACCESS_LOG_LINE = _MakeHttpAccessLogLine()
  _GRPC_ACCESS_LOG_LINE = _MakeGrpcAccessLogLine()

  _LINE_STRUCTURES = [
      ('grpc_access_log', _GRPC_ACCESS_LOG_LINE),
      ('http_access_log', _HTTP_ACCESS_LOG_LINE),
  ]

  VERIFICATION_GRAMMAR = _MakeGrpcAccessLogLine() | _MakeHttpAccessLogLine()

  VERIFICATION_LITERALS = [' | http | ', ' | https | ', ' | ssh | ',
                           ' | grpc | ']

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
    bytes_read = self._GetValueFromStructure(structure, 'bytes_read')
    bytes_written = self._GetValueFromStructure(structure, 'bytes_written')
    status_code = self._GetValueFromStructure(structure, 'status_code')
    request_time = self._GetValueFromStructure(structure, 'request_time')
    labels_raw = self._GetValueFromStructure(
        structure, 'labels', default_value='').strip()
    labels = None if (not labels_raw or labels_raw == '-') else labels_raw
    user_name = self._GetValueFromStructure(structure, 'user_name')
    session_id = self._GetValueFromStructure(structure, 'session_id')
    mesh_execution_id = self._GetValueFromStructure(
        structure, 'mesh_execution_id')

    event_data = BitbucketAccessEventData()
    event_data.remote_address = self._GetValueFromStructure(
        structure, 'remote_address')
    event_data.protocol = self._GetValueFromStructure(structure, 'protocol')
    event_data.request_id = self._GetValueFromStructure(
        structure, 'request_id')
    if event_data.request_id == '-':
      event_data.request_id = None
    event_data.user_name = None if user_name == '-' else user_name
    event_data.session_id = None if session_id == '-' else session_id
    event_data.mesh_execution_id = (
        None if (not mesh_execution_id or mesh_execution_id == '-')
        else mesh_execution_id)
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)

    if http_request:
      event_data.http_request_method = self._GetValueFromStructure(
          http_request, 'http_method')
      event_data.http_request_uri = self._GetValueFromStructure(
          http_request, 'request_url')
      event_data.http_version = self._GetValueFromStructure(
          http_request, 'http_version') or None
      event_data.ssh_repository_path = self._GetValueFromStructure(
          http_request, 'ssh_repo') or None

    event_data.http_request_user_agent = (
        self._GetStringValueFromStructure(structure, 'user_agent') or None)
    event_data.http_response_code = (
        None if status_code == '-' else status_code)
    event_data.http_response_bytes_read = (
        None if bytes_read == '-' else bytes_read)
    event_data.http_response_bytes_written = (
        None if bytes_written == '-' else bytes_written)
    event_data.labels = labels
    event_data.request_time = (
        None if request_time == '-' else request_time)

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
