# -*- coding: utf-8 -*-
"""This file contains a plugin for SSH syslog entries."""

import pyparsing

from plaso.parsers import syslog
from plaso.parsers import text_parser
from plaso.parsers.syslog_plugins import interface


class SSHLoginEvent(syslog.SyslogLineEvent):
  DATA_TYPE = u'syslog:ssh:login'


class SSHPlugin(interface.SyslogPlugin):
  NAME = u'SSH'
  DESCRIPTION = u'Parser for SSH syslog entries'
  REPORTERS = [u'sshd']

  _pyparsing_components = {
    u'username': pyparsing.Word(pyparsing.printables).setResultsName(
        u'username'),
    u'address': pyparsing.Or([
        text_parser.PyparsingConstants.IPV4_ADDRESS,
        text_parser.PyparsingConstants.IPV6_ADDRESS]).setResultsName(u'address'),
    u'port': pyparsing.Word(pyparsing.nums, max=5),
    u'authentication_method': pyparsing.Or([
        pyparsing.Literal(u'password'),
        pyparsing.Literal(u'publickey')]).setResultsName(
            u'authentication_method'),
    u'protocol': pyparsing.Literal(u'ssh2').setResultsName(u'protocol'),
    u'fingerprint': pyparsing.Combine(pyparsing.Literal(u'RSA') + pyparsing.OneOrMore(
        pyparsing.Word(u':' + pyparsing.hexnums))).setResultsName(u'fingerprint'),
  }

  LOGIN_GRAMMAR = (
    pyparsing.Literal(u'Accepted') +
    _pyparsing_components[u'authentication_method'] +
    pyparsing.Literal(u'for') + _pyparsing_components[u'username'] +
    pyparsing.Literal(u'from') + _pyparsing_components[u'address'] +
    pyparsing.Literal(u'port') + _pyparsing_components[u'port'] +
    _pyparsing_components[u'protocol'] +
    pyparsing.Optional(
      pyparsing.Literal(u':') +
      _pyparsing_components[u'fingerprint'])
  )

  # example line:  Accepted publickey for onager from 192.168.192.17 port
  # 59229 ssh2: RSA fc:9c:b6:f7:c8:2c:ac:bb:53:74:ff:3a:03:66:e7:44
  # example line:  Accepted password for onager from
  # fdbd:c75e:bd4b:0:a96b:207c:e517:5ee port 42532  ssh2


  def Process(self, parser_mediator, attributes=None, **kwargs):
    """Process the data"""
