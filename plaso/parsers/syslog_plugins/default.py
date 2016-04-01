# -*- coding: utf-8 -*-
"""This file contains a default plugin for syslog entries."""
from plaso.parsers import syslog_new
from plaso.parsers import syslog
from plaso.parsers.syslog_plugins import interface

class DefaultSyslogPlugin(interface.SyslogPlugin):

  NAME = u'default'
  DESCRIPTION = u'Default plugin for syslog entries'

  def Process(self, parser_mediator, timestamp=None, attributes=None, **kwargs):
    """Process a syslog event."""
    event = syslog.SyslogLineEvent(timestamp, 0, attributes)
    parser_mediator.ProduceEvent(event)

syslog_new.NewSyslogParser.RegisterPlugin(DefaultSyslogPlugin)