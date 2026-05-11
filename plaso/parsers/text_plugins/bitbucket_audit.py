"""Text parser plugin for Atlassian Bitbucket audit log files.

This is for the atlassian-bitbucket-audit.log file, one of multiple log files
produced by a Bitbucket DC/Server installation.

The audit log is a pipe-delimited file with the following fields:
  ip_address | event_name | user | timestamp_ms | entity | details |
  request_identifier | session_identifier

The timestamp field is milliseconds since the Unix epoch (January 1, 1970).

Also see:
  https://support.atlassian.com/bitbucket-data-center/kb/how-to-read-the-bitbucket-data-center-log-formats/
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class BitbucketAuditEventData(events.EventData):
  """Bitbucket audit log event data.

  Attributes:
    details (str): JSON-encoded details of the affected entity.
    entity (str): the affected entity in the format PRODUCT/key, such as
        BITBUCKET/bitbucket or PROJECT/myproject.
    event_name (str): the name of the audited event, such as
        RestrictedRefAddedEvent.
    recorded_time (dfdatetime.DateTimeValues): date and time the audit event
        was recorded.
    remote_address (str): remote IP address(es), including X-Forwarded-For
        proxies. Multiple addresses are comma-separated; the first address is
        the originating IP and the last is the directly connected IP.
    request_identifier (str): unique identifier for the request that triggered
        the audit event, correlatable with the access log.
    session_identifier (str): session identifier, correlatable with the access
        log.
    user_name (str): the name of the user who triggered the event.
  """

  DATA_TYPE = 'atlassian:bitbucket:audit'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.details = None
    self.entity = None
    self.event_name = None
    self.recorded_time = None
    self.remote_address = None
    self.request_identifier = None
    self.session_identifier = None
    self.user_name = None


class BitbucketAuditTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Bitbucket audit log files."""

  NAME = 'bitbucket_audit'
  DATA_FORMAT = (
      'Atlassian Bitbucket audit log (atlassian-bitbucket-audit.log) file')

  ENCODING = 'utf-8'

  # Pipe as field separator.
  _SEPARATOR = pyparsing.Suppress(pyparsing.Literal('|'))

  # Remote IP address field: one or more IPv4/IPv6 addresses separated by
  # commas, such as "63.246.22.199,172.16.1.187" or "0:0:0:0:0:0:0:1"
  _REMOTE_ADDRESS = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphanums + '.:,')
  ).set_results_name('remote_address')

  # Event name: CamelCase Java event class name, such as RestrictedRefAddedEvent
  _EVENT_NAME = pyparsing.Word(
      pyparsing.alphanums + '_').set_results_name('event_name')

  # User name: alphanumeric with dots/hyphens/underscores, or '-'
  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-_./@') |
      pyparsing.Literal('-')).set_results_name('user_name')

  # Timestamp: milliseconds since Unix epoch, such as 1400681361906
  _TIMESTAMP_MS = pyparsing.Word(pyparsing.nums).set_parse_action(
      lambda tokens: int(tokens[0], 10)).set_results_name('timestamp_ms')

  # Entity: PRODUCT/key format, such as BITBUCKET/bitbucket or PROJECT/myproject
  # May also be '-' when not applicable
  _ENTITY = (
      pyparsing.Word(pyparsing.alphanums + '/-_.') |
      pyparsing.Literal('-')).set_results_name('entity')

  # Details: JSON object or array, or '-' when not applicable.
  # Use SkipTo to capture everything up to the next ' | ' separator.
  _DETAILS = pyparsing.SkipTo(
      pyparsing.Literal('|')).set_results_name('details')

  # Request identifier, such as '@8KJQAGx969x538x0', '*1APC3V1x...' or '-'.
  _REQUEST_IDENTIFIER = (
      pyparsing.Word(pyparsing.alphanums + '@*-_x') |
      pyparsing.Literal('-')).set_results_name('request_identifier')

  # Session identifier, short alphanumeric identifier or '-'.
  _SESSION_IDENTIFIER = (
      pyparsing.Word(pyparsing.alphanums + '-_') |
      pyparsing.Literal('-')).set_results_name('session_identifier')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Audit log line format (pipe-delimited):
  # ip_address | event_name | user | timestamp_ms | entity | details |
  # request_identifier | session_identifier
  _AUDIT_LOG_LINE = (
      _REMOTE_ADDRESS + _SEPARATOR +
      _EVENT_NAME + _SEPARATOR +
      _USER_NAME + _SEPARATOR +
      _TIMESTAMP_MS + _SEPARATOR +
      _ENTITY + _SEPARATOR +
      _DETAILS + _SEPARATOR +
      _REQUEST_IDENTIFIER + _SEPARATOR +
      _SESSION_IDENTIFIER +
      _END_OF_LINE)

  _LINE_STRUCTURES = [('audit_entry', _AUDIT_LOG_LINE)]

  VERIFICATION_GRAMMAR = _AUDIT_LOG_LINE

  def _GetDateTimeValue(self, structure, name):
    """Retrieves a date and time value from a Pyparsing structure.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.

    Returns:
      dfdatetime.TimeElements: date and time value or None if not available.
    """
    timestamp = self._GetValueFromStructure(structure, name)
    if not timestamp:
      return None

    return dfdatetime_posix_time.PosixTimeInMilliseconds(
        timestamp=timestamp)

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
    if not value or value == '-':
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
    if key != 'audit_entry':
      raise errors.ParseError(
          f'Unable to parse record, unknown structure: {key:s}')

    details = self._GetValueFromStructure(
        structure, 'details', default_value='').strip()

    event_data = BitbucketAuditEventData()
    event_data.details = None if not details or details == '-' else details
    event_data.entity = self._GetStrippedValue(structure, 'entity')
    event_data.event_name = self._GetValueFromStructure(
        structure, 'event_name')
    event_data.recorded_time = self._GetDateTimeValue(structure, 'timestamp_ms')
    event_data.remote_address = self._GetValueFromStructure(
        structure, 'remote_address')
    event_data.request_identifier = self._GetStrippedValue(
        structure, 'request_identifier')
    event_data.session_identifier = self._GetStrippedValue(
        structure, 'session_identifier')
    event_data.user_name = self._GetStrippedValue(structure, 'user_name')

    parser_mediator.ProduceEventData(event_data)

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

    timestamp_ms = self._GetValueFromStructure(structure, 'timestamp_ms')

    # The timestamp must look like a plausible millisecond epoch value.
    # Reject values that are too small (before year 2000) or too large.
    # Year 2000 in ms = 946684800000; year 2100 in ms = 4102444800000
    if (timestamp_ms is None or
        not 946684800000 <= timestamp_ms <= 4102444800000):
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(BitbucketAuditTextPlugin)
