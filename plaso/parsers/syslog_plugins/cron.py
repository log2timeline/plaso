# -*- coding: utf-8 -*-
"""This file contains a plugin for SSH syslog entries."""

import pyparsing

from plaso.parsers import syslog
from plaso.parsers.syslog_plugins import interface


class CronTaskRunEvent(syslog.SyslogLineEvent):
  """Convenience class for cron task run messages."""
  DATA_TYPE = u'syslog:cron:task_run'


class CronPlugin(interface.SyslogPlugin):
  """A syslog plugin for parsing cron messages."""
  NAME = u'cron'

  DESCRIPTION = u'Parser for syslog cron messages.'

  REPORTER = u'CRON'

  _PYPARSING_COMPONENTS = {
      u'command': pyparsing.Combine(
          pyparsing.SkipTo(
              pyparsing.Literal(u')') + pyparsing.StringEnd())).
                  setResultsName(u'command'),
      u'username': pyparsing.Word(pyparsing.alphanums).setResultsName(
          u'username'),
  }

  _TASK_RUN_GRAMMAR = (
      pyparsing.Literal(u'(') + _PYPARSING_COMPONENTS[u'username'] +
      pyparsing.Literal(u')') + pyparsing.Literal(u'CMD') +
      pyparsing.Literal(u'(') + _PYPARSING_COMPONENTS[u'command'] +
      pyparsing.Literal(u')') + pyparsing.StringEnd()
  )

  MESSAGE_GRAMMARS = [(u'task_run', _TASK_RUN_GRAMMAR)]

  def ParseMessage(self, parser_mediator, key, timestamp, tokens):
    """Parses a syslog body that matched one of defined grammars.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: a string indicating the name of the matching grammar.
      timestamp: the timestamp, which is an integer containing the number
                  of micro seconds since January 1, 1970, 00:00:00 UTC or 0
                  on error.
      tokens: a dictionary containing the results of the syslog grammar, and the
              cron grammar.

    Raises:
      AttributeError: If an unknown key is provided.
    """
    if key == u'task_run':
      parser_mediator.ProduceEvent(CronTaskRunEvent(timestamp, 0, tokens))
    else:
      raise AttributeError(u'Unknown grammar key: {0:s}'.format(key))


syslog.SyslogParser.RegisterPlugin(CronPlugin)
