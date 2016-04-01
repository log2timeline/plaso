# -*- coding: utf-8 -*-
"""This file contains a plugin for SSH syslog entries."""

import pyparsing

from plaso.parsers import syslog
from plaso.parsers import syslog_new
from plaso.parsers import text_parser
from plaso.lib import errors
from plaso.parsers.syslog_plugins import interface


class SSHLoginEvent(syslog.SyslogLineEvent):
  DATA_TYPE = u'syslog:ssh:login'


class SSHPlugin(interface.SyslogPlugin):
  NAME = u'SSH'
  DESCRIPTION = u'Parser for SSH syslog entries'
  REPORTER = u'sshd'

  _PYPARSING_COMPONENTS = {
    u'username': pyparsing.Word(pyparsing.printables).setResultsName(
        u'username'),
    u'address': pyparsing.Or([
        text_parser.PyparsingConstants.IPV4_ADDRESS,
        text_parser.PyparsingConstants.IPV6_ADDRESS]).setResultsName(u'address'),
    u'port': pyparsing.Word(pyparsing.nums, max=5).setResultsName(u'port'),
    u'authentication_method': pyparsing.Or([
        pyparsing.Literal(u'password'),
        pyparsing.Literal(u'publickey')]).setResultsName(
            u'authentication_method'),
    u'protocol': pyparsing.Literal(u'ssh2').setResultsName(u'protocol'),
    u'fingerprint': pyparsing.Combine(pyparsing.Literal(u'RSA') + pyparsing.OneOrMore(
        pyparsing.Word(u':' + pyparsing.hexnums))).setResultsName(u'fingerprint'),
  }

  _LOGIN_GRAMMAR = (
    pyparsing.Literal(u'Accepted') +
    _PYPARSING_COMPONENTS[u'authentication_method'] +
    pyparsing.Literal(u'for') + _PYPARSING_COMPONENTS[u'username'] +
    pyparsing.Literal(u'from') + _PYPARSING_COMPONENTS[u'address'] +
    pyparsing.Literal(u'port') + _PYPARSING_COMPONENTS[u'port'] +
    _PYPARSING_COMPONENTS[u'protocol'] +
    pyparsing.Optional(
      pyparsing.Literal(u':') +
      _PYPARSING_COMPONENTS[u'fingerprint'])
  )

  # example line:  Accepted publickey for onager from 192.168.192.17 port
  # 59229 ssh2: RSA fc:9c:b6:f7:c8:2c:ac:bb:53:74:ff:3a:03:66:e7:44
  # example line:  Accepted password for onager from
  # fdbd:c75e:bd4b:0:a96b:207c:e517:5ee port 42532  ssh2


  def Process(self, parser_mediator, timestamp=None, attributes=None, **kwargs):
    """Process the data

    Args:
      parser_mediator: the parser mediator.
      timestamp: the timestamp of the syslog event.
      attributes: the attributes of the syslog line.
    """
    message = getattr(attributes, u'message')
    if not message:
      raise AttributeError(u'Missing required attribute "message"')

    try:
      ssh_attributes = self._LOGIN_GRAMMAR.parseString(message)
      event = SSHLoginEvent(timestamp, 0, ssh_attributes)
      parser_mediator.ProduceEvent(event)
      return
    except pyparsing.ParseException:
      pass


    raise errors.WrongPlugin(
        u'Unable to extract SSH event from {0:s}'.format(message))

syslog_new.NewSyslogParser.RegisterPlugin(SSHPlugin)