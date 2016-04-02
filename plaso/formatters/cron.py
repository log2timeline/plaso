# -*- coding: utf-8 -*-
"""The syslog cron formatters."""

from plaso.formatters import interface
from plaso.formatters import manager


class CronTaskRunEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a syslog cron task run event."""

  DATA_TYPE = u'syslog:cron:task_run'

  FORMAT_STRING_SEPARATOR = u' '

  FORMAT_STRING_PIECES = [
      u'Cron ran: {command}',
      u'for user: {username}',
      u'pid: {pid}']

  FORMAT_STRING_SHORT = u'{body}'

  SOURCE_LONG = u'Cron log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(CronTaskRunEventFormatter)
