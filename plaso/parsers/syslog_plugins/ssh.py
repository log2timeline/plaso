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

  DATA_TYPE = u'syslog:ssh:login'


class SSHFailedConnectionEventData(SSHEventData):
  """SSH failed connection event data."""

  DATA_TYPE = u'syslog:ssh:failed_connection'


class SSHOpenedConnectionEventData(SSHEventData):
  """SSH opened connection event data."""

  DATA_TYPE = u'syslog:ssh:opened_connection'


class SSHPlugin(interface.SyslogPlugin):
  """A plugin for creating events from syslog message produced by SSH."""
  NAME = u'ssh'
  DESCRIPTION = u'Parser for SSH syslog entries.'
  REPORTER = u'sshd'

  _AUTHENTICATION_METHOD = (
      pyparsing.Keyword(u'password') | pyparsing.Keyword(u'publickey'))

  _PYPARSING_COMPONENTS = {
      u'address': text_parser.PyparsingConstants.IP_ADDRESS.setResultsName(
          u'address'),
      u'authentication_method': _AUTHENTICATION_METHOD.setResultsName(
          u'authentication_method'),
      u'fingerprint': pyparsing.Combine(
          pyparsing.Literal(u'RSA ') +
          pyparsing.Word(u':' + pyparsing.hexnums)).setResultsName(
              u'fingerprint'),
      u'port': pyparsing.Word(pyparsing.nums, max=5).setResultsName(u'port'),
      u'protocol': pyparsing.Literal(u'ssh2').setResultsName(u'protocol'),
      u'username': pyparsing.Word(pyparsing.alphanums).setResultsName(
          u'username'),
  }

  _LOGIN_GRAMMAR = (
      pyparsing.Literal(u'Accepted') +
      _PYPARSING_COMPONENTS[u'authentication_method'] +
      pyparsing.Literal(u'for') + _PYPARSING_COMPONENTS[u'username'] +
      pyparsing.Literal(u'from') + _PYPARSING_COMPONENTS[u'address'] +
      pyparsing.Literal(u'port') + _PYPARSING_COMPONENTS[u'port'] +
      _PYPARSING_COMPONENTS[u'protocol'] +
      pyparsing.Optional(
          pyparsing.Literal(u':') + _PYPARSING_COMPONENTS[u'fingerprint']) +
      pyparsing.StringEnd()
  )

  _FAILED_CONNECTION_GRAMMAR = (
      pyparsing.Literal(u'Failed') +
      _PYPARSING_COMPONENTS[u'authentication_method'] +
      pyparsing.Literal(u'for') + _PYPARSING_COMPONENTS[u'username'] +
      pyparsing.Literal(u'from') + _PYPARSING_COMPONENTS[u'address'] +
      pyparsing.Literal(u'port') + _PYPARSING_COMPONENTS[u'port'] +
      pyparsing.StringEnd()
  )

  _OPENED_CONNECTION_GRAMMAR = (
      pyparsing.Literal(u'Connection from') +
      _PYPARSING_COMPONENTS[u'address'] +
      pyparsing.Literal(u'port') + _PYPARSING_COMPONENTS[u'port'] +
      pyparsing.LineEnd()
  )

  MESSAGE_GRAMMARS = [
      (u'login', _LOGIN_GRAMMAR),
      (u'failed_connection', _FAILED_CONNECTION_GRAMMAR),
      (u'opened_connection', _OPENED_CONNECTION_GRAMMAR),]

  def ParseMessage(self, parser_mediator, key, timestamp, tokens):
    """Produces an event from a syslog body that matched one of the grammars.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the matching grammar.
      timestamp (int): the timestamp, which contains the number of micro seconds
          since January 1, 1970, 00:00:00 UTC or 0 on error.
      tokens (dict[str, str]): tokens derived from a syslog message based on
          the defined grammar.

    Raises:
      AttributeError: If an unknown key is provided.
    """
    # TODO: change AttributeError into ValueError or equiv.
    if key not in (u'failed_connection', u'login', u'opened_connection'):
      raise AttributeError(u'Unknown grammar key: {0:s}'.format(key))

    if key == u'login':
      event_data = SSHLoginEventData()

    elif key == u'failed_connection':
      event_data = SSHFailedConnectionEventData()

    elif key == u'opened_connection':
      event_data = SSHOpenedConnectionEventData()

    event_data.address = tokens.get(u'address', None)
    event_data.authentication_method = tokens.get(
        u'authentication_method', None)
    event_data.body = tokens.get(u'body', None)
    event_data.fingerprint = tokens.get(u'fingerprint', None)
    event_data.hostname = tokens.get(u'hostname', None)
    # TODO: pass line number to offset or remove.
    event_data.offset = 0
    event_data.pid = tokens.get(u'pid', None)
    event_data.protocol = tokens.get(u'protocol', None)
    event_data.port = tokens.get(u'port', None)
    event_data.reporter = tokens.get(u'reporter', None)
    event_data.severity = tokens.get(u'severity', None)
    event_data.username = tokens.get(u'username', None)

    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


syslog.SyslogParser.RegisterPlugin(SSHPlugin)
