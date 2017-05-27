# -*- coding: utf-8 -*-
"""This file contains a plugin for SSH syslog entries."""

import pyparsing

from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import syslog
from plaso.parsers.syslog_plugins import interface


class CronTaskRunEventData(syslog.SyslogLineEventData):
  """Cron task run event data.

  Attributes:
    command (str): command executed.
    username (str): name of user the command was executed.
  """

  DATA_TYPE = u'syslog:cron:task_run'

  def __init__(self):
    """Initializes event data."""
    super(CronTaskRunEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.username = None


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
    if key != u'task_run':
      raise AttributeError(u'Unknown grammar key: {0:s}'.format(key))

    event_data = CronTaskRunEventData()
    event_data.body = tokens.get(u'body', None)
    event_data.command = tokens.get(u'command', None)
    event_data.hostname = tokens.get(u'hostname', None)
    # TODO: pass line number to offset or remove.
    event_data.offset = 0
    event_data.pid = tokens.get(u'pid', None)
    event_data.reporter = tokens.get(u'reporter', None)
    event_data.severity = tokens.get(u'severity', None)
    event_data.username = tokens.get(u'username', None)

    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


syslog.SyslogParser.RegisterPlugin(CronPlugin)
