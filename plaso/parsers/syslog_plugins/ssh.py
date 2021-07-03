# -*- coding: utf-8 -*-
"""This file contains a plugin for SSH syslog entries."""

import pyparsing

from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import syslog
from plaso.parsers import text_parser
from plaso.parsers.syslog_plugins import interface


class SSHEventData(syslog.SyslogLineEventData):
  """SSH event data.

  Attributes:
    address (str): IP address.
    authentication_method (str): authentication method.
    fingerprint (str): fingerprint.
    port (str): port.
    protocol (str): protocol.
    username (str): name of user the command was executed.
  """

  def __init__(self):
    """Initializes event data."""
    super(SSHEventData, self).__init__(data_type=self.DATA_TYPE)
    self.address = None
    self.authentication_method = None
    self.fingerprint = None
    self.port = None
    self.protocol = None
    self.username = None


# TODO: merge separate SSHEventData classes.
class SSHLoginEventData(SSHEventData):
  """SSH login event data."""

  DATA_TYPE = 'syslog:ssh:login'


class SSHFailedConnectionEventData(SSHEventData):
  """SSH failed connection event data."""

  DATA_TYPE = 'syslog:ssh:failed_connection'


class SSHOpenedConnectionEventData(SSHEventData):
  """SSH opened connection event data."""

  DATA_TYPE = 'syslog:ssh:opened_connection'


class SSHSyslogPlugin(interface.SyslogPlugin):
  """A plugin for creating events from syslog message produced by SSH."""

  NAME = 'ssh'
  DATA_FORMAT = 'SSH syslog line'

  REPORTER = 'sshd'

  _AUTHENTICATION_METHOD = (
      pyparsing.Keyword('password') | pyparsing.Keyword('publickey'))

  _PYPARSING_COMPONENTS = {
      'address': text_parser.PyparsingConstants.IP_ADDRESS.setResultsName(
          'address'),
      'authentication_method': _AUTHENTICATION_METHOD.setResultsName(
          'authentication_method'),
      'fingerprint': pyparsing.Combine(
          pyparsing.Literal('RSA ') +
          pyparsing.Word(':' + pyparsing.hexnums)).setResultsName(
              'fingerprint'),
      'port': pyparsing.Word(pyparsing.nums, max=5).setResultsName('port'),
      'protocol': pyparsing.Literal('ssh2').setResultsName('protocol'),
      'username': pyparsing.Word(pyparsing.alphanums).setResultsName(
          'username'),
  }

  _LOGIN_GRAMMAR = (
      pyparsing.Literal('Accepted') +
      _PYPARSING_COMPONENTS['authentication_method'] +
      pyparsing.Literal('for') + _PYPARSING_COMPONENTS['username'] +
      pyparsing.Literal('from') + _PYPARSING_COMPONENTS['address'] +
      pyparsing.Literal('port') + _PYPARSING_COMPONENTS['port'] +
      _PYPARSING_COMPONENTS['protocol'] +
      pyparsing.Optional(
          pyparsing.Literal(':') + _PYPARSING_COMPONENTS['fingerprint']) +
      pyparsing.StringEnd()
  )

  _FAILED_CONNECTION_GRAMMAR = (
      pyparsing.Literal('Failed') +
      _PYPARSING_COMPONENTS['authentication_method'] +
      pyparsing.Literal('for') + _PYPARSING_COMPONENTS['username'] +
      pyparsing.Literal('from') + _PYPARSING_COMPONENTS['address'] +
      pyparsing.Literal('port') + _PYPARSING_COMPONENTS['port'] +
      pyparsing.StringEnd()
  )

  _OPENED_CONNECTION_GRAMMAR = (
      pyparsing.Literal('Connection from') +
      _PYPARSING_COMPONENTS['address'] +
      pyparsing.Literal('port') + _PYPARSING_COMPONENTS['port'] +
      pyparsing.LineEnd()
  )

  MESSAGE_GRAMMARS = [
      ('login', _LOGIN_GRAMMAR),
      ('failed_connection', _FAILED_CONNECTION_GRAMMAR),
      ('opened_connection', _OPENED_CONNECTION_GRAMMAR),]

  def _ParseMessage(self, parser_mediator, key, date_time, tokens):
    """Produces an event from a syslog body that matched one of the grammars.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the matching grammar.
      date_time (dfdatetime.DateTimeValues): date and time values.
      tokens (dict[str, str]): tokens derived from a syslog message based on
          the defined grammar.

    Raises:
      ValueError: If an unknown key is provided.
    """
    if key not in ('failed_connection', 'login', 'opened_connection'):
      raise ValueError('Unknown grammar key: {0:s}'.format(key))

    if key == 'login':
      event_data = SSHLoginEventData()

    elif key == 'failed_connection':
      event_data = SSHFailedConnectionEventData()

    elif key == 'opened_connection':
      event_data = SSHOpenedConnectionEventData()

    event_data.address = tokens.get('address', None)
    event_data.authentication_method = tokens.get(
        'authentication_method', None)
    event_data.body = tokens.get('body', None)
    event_data.fingerprint = tokens.get('fingerprint', None)
    event_data.hostname = tokens.get('hostname', None)
    event_data.pid = tokens.get('pid', None)
    event_data.protocol = tokens.get('protocol', None)
    event_data.port = tokens.get('port', None)
    event_data.reporter = tokens.get('reporter', None)
    event_data.severity = tokens.get('severity', None)
    event_data.username = tokens.get('username', None)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)


syslog.SyslogParser.RegisterPlugin(SSHSyslogPlugin)
