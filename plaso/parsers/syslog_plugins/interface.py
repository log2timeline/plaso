# -*- coding: utf-8 -*-
"""This file contains an interface for syslog plugins."""

import abc

from plaso.parsers import plugins

class SyslogPlugin(plugins.BasePlugin):
  """The interface for syslog plugins."""
  NAME = u'syslog'
  DESCRIPTION = u''

  # The syslog reporter string that the plugin replies to.
  REPORTER = u''

  @abc.abstractmethod
  def Process(
        self, parser_mediator, timestamp=None, attributes=None,
        **kwargs):
    """Processes the data structure produced by the parser.

    Args:
      parser_mediator:
      timestamp:
      attributes:
      """