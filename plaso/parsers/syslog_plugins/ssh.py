# -*- coding: utf-8 -*-
"""This file contains a plugin for SSH syslog entries."""

import pyparsing

from plaso.parsers import syslog
from plaso.parsers import text_parser
from plaso.parsers.syslog_plugins import interface


class SSHLoginEvent(syslog.SyslogLineEvent):
  """Convenience class for a SSH login event."""
  DATA_TYPE = u'syslog:ssh:login'


class SSHFailedConnectionEvent(syslog.SyslogLineEvent):
  """Convenience class for a SSH failed connection event."""
  DATA_TYPE = u'syslog:ssh:failed_connection'


class SSHOpenedConnectionEvent(syslog.SyslogLineEvent):
  """Convenience class for a SSH opened connection event."""
  DATA_TYPE = u'syslog:ssh:opened_connection'


class SSHPlugin(interface.SyslogPlugin):
  """A plugin for creating events from syslog message produced by SSH."""
  NAME = u'ssh'
  DESCRIPTION = u'Parser for SSH syslog entries.'
  REPORTER = u'sshd'

  _PYPARSING_COMPONENTS = {
      u'username': pyparsing.Word(pyparsing.alphanums).setResultsName(
          u'username'),
      u'address': pyparsing.Or([
          text_parser.PyparsingConstants.IPV4_ADDRESS,
          text_parser.PyparsingConstants.IPV6_ADDRESS]).
                  setResultsName(u'address'),
      u'port': pyparsing.Word(pyparsing.nums, max=5).setResultsName(u'port'),
      u'authentication_method': pyparsing.Or([
          pyparsing.Literal(u'password'),
          pyparsing.Literal(u'publickey')]).setResultsName(
              u'authentication_method'),
      u'protocol': pyparsing.Literal(u'ssh2').setResultsName(u'protocol'),
      u'fingerprint': (pyparsing.Combine(
          pyparsing.Literal(u'RSA ') +
          pyparsing.Word(u':' + pyparsing.hexnums))).
                      setResultsName(u'fingerprint'),
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
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: an string indicating the name of the matching grammar.
      timestamp: the timestamp, which is an integer containing the number
                  of micro seconds since January 1, 1970, 00:00:00 UTC or 0
                  on error.
      tokens: a dictionary containing the results of the syslog grammar, and the
              ssh grammar.

    Raises:
      AttributeError: If an unknown key is provided.
    """
    if key == u'login':
      event_object = SSHLoginEvent(timestamp, 0, tokens)

    elif key == u'failed_connection':
      event_object = SSHFailedConnectionEvent(timestamp, 0, tokens)

    elif key == u'opened_connection':
      event_object = SSHOpenedConnectionEvent(timestamp, 0, tokens)

    else:
      raise AttributeError(u'Unknown grammar key: {0:s}'.format(key))

    parser_mediator.ProduceEvent(event_object)


syslog.SyslogParser.RegisterPlugin(SSHPlugin)
