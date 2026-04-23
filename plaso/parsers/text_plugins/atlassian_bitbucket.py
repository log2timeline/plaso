# -*- coding: utf-8 -*-
"""Text parser plugin for Atlassian Bitbucket log files.

This is for the atlassian-bitbucket.log file, one of multiple log files
produced by a Bitbucket DC/Server installation.

The default log format (logback pattern: %date %-5level [%thread] %request
%logger{36} %m%n%eThrowable) produces lines of the form:

  YYYY-MM-DD HH:MM:SS,mmm LEVEL [thread] logger_class message

With the optional %request context fields between [thread] and logger_class:

  YYYY-MM-DD HH:MM:SS,mmm LEVEL [thread] user request_id session_id ip "action" logger_class message

All %request fields are optional and may be absent. In practice, lines often
omit some or all of these fields depending on the context of the log event.

Also see:
  https://support.atlassian.com/bitbucket-data-center/kb/how-to-read-the-bitbucket-data-center-log-formats/
  https://support.atlassian.com/bitbucket-data-center/kb/how-to-change-the-bitbucket-application-log-format/
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class AtlassianBitbucketEventData(events.EventData):
  """Bitbucket application log event data.

  Attributes:
    body (str): the freeform body of the log line (the log message).
    ip_address (str): the client IP address associated with the request, if
        present in the log line.
    level (str): the logging level of the event (e.g. INFO, WARN, ERROR).
    logger_class (str): the abbreviated or full class name responsible for
        logging the event (e.g. c.a.b.m.r.DefaultRepositoryManager).
    request_action (str): the request action string (e.g.
        "TransactionService/Transact"), if present.
    request_id (str): the unique request identifier (e.g.
        2CM38K4Fx339x113x2), if present.
    session_id (str): the session identifier, if present.
    thread (str): the JVM thread name from which the log event originated.
    user_name (str): the name of the user associated with the request, if
        present in the log line.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'atlassian:bitbucket:line'

  def __init__(self):
    """Initializes event data."""
    super(AtlassianBitbucketEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.body = None
    self.ip_address = None
    self.level = None
    self.logger_class = None
    self.request_action = None
    self.request_id = None
    self.session_id = None
    self.thread = None
    self.user_name = None
    self.written_time = None


class AtlassianBitbucketTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Bitbucket log files."""

  NAME = 'atlassian_bitbucket'
  DATA_FORMAT = 'Atlassian Bitbucket log file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  # Bitbucket log levels.
  _BITBUCKET_LEVELS = ['DEBUG', 'ERROR', 'FATAL', 'INFO', 'TRACE', 'WARN']

  # Date and time format: 2020-09-08 07:53:45,084
  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      pyparsing.Suppress('-') + _TWO_DIGITS + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(',') + _THREE_DIGITS).set_results_name(
          'date_time')

  # Log level (DEBUG, ERROR, FATAL, INFO, TRACE, WARN).
  _LOG_LEVEL = pyparsing.oneOf(_BITBUCKET_LEVELS).set_results_name('level')

  # Thread name enclosed in brackets. Thread names can contain brackets
  # themselves (e.g. sshd-SshServer[1aa226b3](port=7999)-nio2-thread-3),
  # so use SkipTo to find the last ']' before the level/logger fields.
  _BITBUCKET_THREAD = (
      pyparsing.Suppress('[') +
      pyparsing.SkipTo(']').set_results_name('thread') +
      pyparsing.Suppress(']'))

  # Optional %request context fields that appear between [thread] and
  # logger_class. These are produced by logback's %request converter.
  # Format: user request_id session_id ip_address "action"
  #
  # user: alphanumeric with hyphens/dots/underscores, or absent.
  # request_id: hex-like token e.g. 2CM38K4Fx339x113x2, or absent.
  # session_id: short alphanumeric, or absent (may be comma-separated with
  #             a second mesh ID, e.g. @5XDWX5x339x568x0,4SJOMSOBx339x40x2).
  # ip_address: IPv4/IPv6 address, or absent.
  # action: quoted string e.g. "TransactionService/Transact", or absent.
  #
  # Because all fields are optional and the boundary between them and the
  # logger class is ambiguous, we use SkipTo to capture the logger class
  # (dotted/abbreviated class name) as the anchor point, then parse the
  # preceding %request fields out of the captured text.

  # Logger class: abbreviated or full Java class name.
  # Matches patterns like: c.a.b.m.r.DefaultRepositoryManager,
  # com.atlassian.bitbucket.internal.boot.log.BuildInfoLogger,
  # o.h.i.ExceptionMapperStandardImpl, org.hibernate.SQL
  _BITBUCKET_LOGGER = (
      pyparsing.Word(
          pyparsing.alphanums + '._$').set_results_name('logger_class'))

  # The %request user field: matches a non-hyphen-starting word that looks
  # like a username (alphanumeric, dots, hyphens, underscores, slashes).
  _REQUEST_USER = pyparsing.Word(
      pyparsing.alphanums + '-_./').set_results_name('request_user')

  # Request ID: alphanumeric token with 'x' separators, e.g. 2CM38K4Fx339x113x2
  _REQUEST_ID = pyparsing.Word(
      pyparsing.alphanums + 'x').set_results_name('request_id')

  # Session ID: short alphanumeric with optional comma-separated mesh ID,
  # e.g. @5XDWX5x339x568x0 or @5XDWX5x339x568x0,4SJOMSOBx339x40x2
  _SESSION_ID = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphanums + '@*-_x') +
      pyparsing.Optional(
          pyparsing.Literal(',') +
          pyparsing.Word(pyparsing.alphanums + '@*-_x'))
  ).set_results_name('session_id')

  # IP address: IPv4 or IPv6.
  _IP_ADDRESS = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphanums + '.:')
  ).set_results_name('ip_address')

  # Quoted request action: "TransactionService/Transact" or
  # "POST /rest/api/... HTTP/1.1" etc.
  _REQUEST_ACTION = pyparsing.QuotedString('"').set_results_name(
      'request_action')

  # Optional %request context block: all fields optional.
  _REQUEST_CONTEXT = pyparsing.Optional(
      pyparsing.Group(
          pyparsing.Optional(_REQUEST_USER) &
          pyparsing.Optional(_REQUEST_ID) &
          pyparsing.Optional(_SESSION_ID) &
          pyparsing.Optional(_IP_ADDRESS) &
          pyparsing.Optional(_REQUEST_ACTION)
      ).set_results_name('request_context'))

  # Log message body: rest of line.
  _BITBUCKET_LOG_MESSAGE = pyparsing.SkipTo(
      pyparsing.LineEnd()).set_results_name('body')

  # Complete log line structure:
  # <timestamp> <level> [<thread>] [optional request context] <logger> <body>
  _BITBUCKET_LOG_LINE = (
      _DATE_TIME + _LOG_LEVEL + _BITBUCKET_THREAD +
      _REQUEST_CONTEXT + _BITBUCKET_LOGGER + _BITBUCKET_LOG_MESSAGE)

  _LINE_STRUCTURES = [('log_entry', _BITBUCKET_LOG_LINE)]

  VERIFICATION_GRAMMAR = _BITBUCKET_LOG_LINE

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
    if key != 'log_entry':
      raise errors.ParseError(
          f'Unable to parse record, unknown structure: {key:s}')

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    request_context = self._GetValueFromStructure(structure, 'request_context')

    event_data = AtlassianBitbucketEventData()
    event_data.body = self._GetValueFromStructure(
        structure, 'body', default_value='').strip() or None
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.logger_class = self._GetValueFromStructure(
        structure, 'logger_class')
    event_data.thread = self._GetValueFromStructure(structure, 'thread')

    if request_context:
      user_name = self._GetValueFromStructure(request_context, 'request_user')
      event_data.user_name = user_name or None
      event_data.request_id = self._GetValueFromStructure(
          request_context, 'request_id') or None
      event_data.session_id = self._GetValueFromStructure(
          request_context, 'session_id') or None
      event_data.ip_address = self._GetValueFromStructure(
          request_context, 'ip_address') or None
      event_data.request_action = self._GetValueFromStructure(
          request_context, 'request_action') or None

    event_data.written_time = self._ParseTimeElements(time_elements_structure)

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


text_parser.TextLogParser.RegisterPlugin(AtlassianBitbucketTextPlugin)
