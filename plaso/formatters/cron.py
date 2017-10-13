# -*- coding: utf-8 -*-
"""The syslog cron formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class CronTaskRunEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a syslog cron task run event."""

  DATA_TYPE = 'syslog:cron:task_run'

  FORMAT_STRING_SEPARATOR = ' '

  FORMAT_STRING_PIECES = [
      'Cron ran: {command}',
      'for user: {username}',
      'pid: {pid}']

  FORMAT_STRING_SHORT = '{body}'

  SOURCE_LONG = 'Cron log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(CronTaskRunEventFormatter)
