# -*- coding: utf-8 -*-
"""This file contains an interface for syslog plugins."""

import abc

from plaso.lib import errors
from plaso.parsers import plugins

class BaseSyslogPlugin(plugins.BasePlugin):
  """The interface for syslog plugins."""
  NAME = u'syslog'
  DESCRIPTION = u''

  @abc.abstractmethod
  def GetEntries(self, parser_mediator, pyparsing_structure, **kwargs):
    """Creates events from a parsed syslog line."""
