# -*- coding: utf-8 -*-
"""This file contains an interface for syslog plugins."""

import abc

from plaso.parsers import plugins

class SyslogPlugin(plugins.BasePlugin):
  """The interface for syslog plugins."""
  NAME = u'syslog'
  DESCRIPTION = u''

  # A dictionary containing syslog reporters to match on.
  REPORTERS = []

  @abc.abstractmethod
  def Process(self, parser_mediator, attributes=None, **kwargs):
    """Processes the data structure produced by the parser"""