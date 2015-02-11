# -*- coding: utf-8 -*-
"""Formatter for Task Scheduler events."""

from plaso.formatters import interface
from plaso.formatters import manager


class TaskCacheEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a generic Task Cache event."""

  DATA_TYPE = 'task_scheduler:task_cache:entry'

  FORMAT_STRING_PIECES = [
      u'Task: {task_name}',
      u'[Identifier: {task_identifier}]']

  FORMAT_STRING_SHORT_PIECES = [
      u'Task: {task_name}']

  SOURCE_LONG = 'Task Cache'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(TaskCacheEventFormatter)
