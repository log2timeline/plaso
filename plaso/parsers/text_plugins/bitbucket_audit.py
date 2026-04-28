# -*- coding: utf-8 -*-
"""Text parser plugin for Atlassian Bitbucket audit log files.

This is for the atlassian-bitbucket-audit.log file, one of multiple log files
produced by a Bitbucket DC/Server installation.

The audit log is a pipe-delimited file with the following fields:
  ip_address | event_name | user | timestamp_ms | entity | details |
  request_id | session_id

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
    entity (str): the affected entity in the format PRODUCT/key (e.g.
        BITBUCKET/bitbucket, PROJECT/myproject).
    event_name (str): the name of the audited event (e.g.
        RestrictedRefAddedEvent).
    recorded_time (dfdatetime.DateTimeValues): date and time the audit event
        was recorded.
    remote_address (str): remote IP address(es), including X-Forwarded-For
        proxies. Multiple addresses are comma-separated; the first address is
        the originating IP and the last is the directly connected IP.
    request_id (str): unique identifier for the request that triggered the
        audit event, correlatable with the access log.
    session_id (str): session identifier, correlatable with the access log.
    user_name (str): the name of the user who triggered the event.
  """

  DATA_TYPE = 'atlassian:bitbucket:audit'

  def __init__(self):
    """Initializes event data."""
    super(BitbucketAuditEventData, self).__init__(data_type=self.DATA_TYPE)
    self.details = None
    self.entity = None
    self.event_name = None
    self.recorded_time = None
    self.remote_address = None
    self.request_id = None
    self.session_id = None
    self.user_name = None


class BitbucketAuditTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Bitbucket audit log files."""

  NAME = 'bitbucket_audit'
  DATA_FORMAT = (
      'Atlassian Bitbucket audit log (atlassian-bitbucket-audit.log) file')

  ENCODING = 'utf-8'

  _SEP = pyparsing.Suppress(pyparsing.Literal('|'))

  # Remote IP address field: one or more IPv4/IPv6 addresses separated by
  # commas, e.g. "63.246.22.199,172.16.1.187" or "0:0:0:0:0:0:0:1"
  _REMOTE_ADDRESS = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphanums + '.:,')
  ).set_results_name('remote_address')

  # Event name: CamelCase Java event class name, e.g. RestrictedRefAddedEvent
  _EVENT_NAME = pyparsing.Word(
      pyparsing.alphanums + '_').set_results_name('event_name')

  # User name: alphanumeric with dots/hyphens/underscores, or '-'
  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-_./@') |
      pyparsing.Literal('-')).set_results_name('user_name')

  # Timestamp: milliseconds since Unix epoch, e.g. 1400681361906
  _TIMESTAMP_MS = pyparsing.Word(pyparsing.nums).set_parse_action(
      lambda tokens: int(tokens[0], 10)).set_results_name('timestamp_ms')

  # Entity: PRODUCT/key format, e.g. BITBUCKET/bitbucket, PROJECT/myproject
  # May also be '-' when not applicable
  _ENTITY = (
      pyparsing.Word(pyparsing.alphanums + '/-_.') |
      pyparsing.Literal('-')).set_results_name('entity')

  # Details: JSON object or array, or '-' when not applicable.
  # Use SkipTo to capture everything up to the next ' | ' separator.
  _DETAILS = pyparsing.SkipTo(
      pyparsing.Literal('|')).set_results_name('details')

  # Request ID: e.g. @8KJQAGx969x538x0, *1APC3V1x..., or '-'
  _REQUEST_ID = (
      pyparsing.Word(pyparsing.alphanums + '@*-_x') |
      pyparsing.Literal('-')).set_results_name('request_id')

  # Session ID: short alphanumeric identifier, or '-'
  _SESSION_ID = (
      pyparsing.Word(pyparsing.alphanums + '-_') |
      pyparsing.Literal('-')).set_results_name('session_id')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Audit log line format (pipe-delimited):
  # ip_address | event_name | user | timestamp_ms | entity | details |
  # request_id | session_id
  _AUDIT_LOG_LINE = (
      _REMOTE_ADDRESS + _SEP +
      _EVENT_NAME + _SEP +
      _USER_NAME + _SEP +
      _TIMESTAMP_MS + _SEP +
      _ENTITY + _SEP +
      _DETAILS + _SEP +
      _REQUEST_ID + _SEP +
      _SESSION_ID +
      _END_OF_LINE)

  _LINE_STRUCTURES = [('audit_entry', _AUDIT_LOG_LINE)]

  VERIFICATION_GRAMMAR = _AUDIT_LOG_LINE


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

    timestamp_ms = self._GetValueFromStructure(structure, 'timestamp_ms')

    details_raw = self._GetValueFromStructure(
        structure, 'details', default_value='').strip()
    entity = self._GetValueFromStructure(structure, 'entity')
    request_id = self._GetValueFromStructure(structure, 'request_id')
    session_id = self._GetValueFromStructure(structure, 'session_id')
    user_name = self._GetValueFromStructure(structure, 'user_name')

    event_data = BitbucketAuditEventData()
    event_data.remote_address = self._GetValueFromStructure(
        structure, 'remote_address')
    event_data.event_name = self._GetValueFromStructure(
        structure, 'event_name')
    event_data.user_name = None if user_name == '-' else user_name
    event_data.entity = None if entity == '-' else entity
    event_data.details = (
        None if (not details_raw or details_raw == '-') else details_raw)
    event_data.request_id = None if request_id == '-' else request_id
    event_data.session_id = None if session_id == '-' else session_id
    event_data.recorded_time = self._ParseTimestamp(timestamp_ms)

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimestamp(self, timestamp_ms):
    """Parses a Unix millisecond timestamp.

    Args:
      timestamp_ms (int): number of milliseconds since January 1, 1970.

    Returns:
      dfdatetime.PosixTimeInMilliseconds: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the timestamp.
    """
    try:
      date_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
          timestamp=timestamp_ms)

      return date_time
    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse timestamp with error: {exception!s}')

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

    try:
      self._ParseTimestamp(timestamp_ms)
    except errors.ParseError:
      return False

    # The timestamp must look like a plausible millisecond epoch value.
    # Reject values that are too small (before year 2000) or too large.
    # Year 2000 in ms = 946684800000; year 2100 in ms = 4102444800000
    if not 946684800000 <= timestamp_ms <= 4102444800000:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(BitbucketAuditTextPlugin)
