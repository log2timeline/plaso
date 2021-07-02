# -*- coding: utf-8 -*-
"""This file contains a plugin for cron syslog entries."""

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

  DATA_TYPE = 'syslog:cron:task_run'

  def __init__(self):
    """Initializes event data."""
    super(CronTaskRunEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.username = None


class CronSyslogPlugin(interface.SyslogPlugin):
  """A syslog plugin for parsing cron messages."""

  NAME = 'cron'
  DATA_FORMAT = 'Cron syslog line'

  REPORTER = 'CRON'

  _PYPARSING_COMPONENTS = {
      'command': pyparsing.Combine(
          pyparsing.SkipTo(
              pyparsing.Literal(')') + pyparsing.StringEnd())).setResultsName(
                  'command'),
      'username': pyparsing.Word(pyparsing.alphanums).setResultsName(
          'username'),
  }

  _TASK_RUN_GRAMMAR = (
      pyparsing.Literal('(') + _PYPARSING_COMPONENTS['username'] +
      pyparsing.Literal(')') + pyparsing.Literal('CMD') +
      pyparsing.Literal('(') + _PYPARSING_COMPONENTS['command'] +
      pyparsing.Literal(')') + pyparsing.StringEnd()
  )

  MESSAGE_GRAMMARS = [('task_run', _TASK_RUN_GRAMMAR)]

  def _ParseMessage(self, parser_mediator, key, date_time, tokens):
    """Parses a syslog body that matched one of defined grammars.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the matching grammar.
      date_time (dfdatetime.DateTimeValues): date and time values.
      tokens (dict[str, str]): tokens derived from a syslog message based on
          the defined grammar.

    Raises:
      ValueError: If an unknown key is provided.
    """
    if key != 'task_run':
      raise ValueError('Unknown grammar key: {0:s}'.format(key))

    event_data = CronTaskRunEventData()
    event_data.body = tokens.get('body', None)
    event_data.command = tokens.get('command', None)
    event_data.hostname = tokens.get('hostname', None)
    event_data.pid = tokens.get('pid', None)
    event_data.reporter = tokens.get('reporter', None)
    event_data.severity = tokens.get('severity', None)
    event_data.username = tokens.get('username', None)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)


syslog.SyslogParser.RegisterPlugin(CronSyslogPlugin)
