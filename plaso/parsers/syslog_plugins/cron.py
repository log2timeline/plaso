# -*- coding: utf-8 -*-
"""This file contains a plugin for cron syslog entries."""

import pyparsing

from plaso.lib import errors
from plaso.parsers import syslog
from plaso.parsers.syslog_plugins import interface


class CronTaskRunEventData(syslog.SyslogLineEventData):
  """Cron task run event data.

  Attributes:
    command (str): command executed.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    username (str): name of user the command was executed.
  """

  DATA_TYPE = 'syslog:cron:task_run'

  def __init__(self):
    """Initializes event data."""
    super(CronTaskRunEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.last_written_time = None
    self.username = None


class CronSyslogPlugin(interface.SyslogPlugin):
  """A syslog plugin for parsing cron messages."""

  NAME = 'cron'
  DATA_FORMAT = 'Cron syslog line'

  REPORTER = 'CRON'

  _USERNAME = (
      pyparsing.Literal('(') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('username') +
      pyparsing.Literal(')'))

  _COMMAND = (
      pyparsing.Literal('CMD') + pyparsing.Literal('(') +
      pyparsing.Combine(pyparsing.SkipTo(
          pyparsing.Literal(')') +
          pyparsing.StringEnd())).setResultsName('command') +
      pyparsing.Literal(')'))

  _TASK_RUN = _USERNAME + _COMMAND + pyparsing.StringEnd()

  MESSAGE_GRAMMARS = [('task_run', _TASK_RUN)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in MESSAGE_GRAMMARS])

  def _ParseMessage(self, parser_mediator, key, date_time, tokens):
    """Parses a syslog body that matched one of defined grammars.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the matching grammar.
      date_time (dfdatetime.DateTimeValues): date and time values.
      tokens (dict[str, str]): tokens derived from a syslog message based on
          the defined grammar.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse message, unknown structure: {0:s}'.format(key))

    event_data = CronTaskRunEventData()
    event_data.body = tokens.get('body', None)
    event_data.command = tokens.get('command', None)
    event_data.hostname = tokens.get('hostname', None)
    event_data.last_written_time = date_time
    event_data.pid = tokens.get('pid', None)
    event_data.reporter = tokens.get('reporter', None)
    event_data.severity = tokens.get('severity', None)
    event_data.username = tokens.get('username', None)

    parser_mediator.ProduceEventData(event_data)


syslog.SyslogParser.RegisterPlugin(CronSyslogPlugin)
