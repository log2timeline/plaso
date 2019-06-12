# -*- coding: utf-8 -*-
"""The Task Scheduler event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TaskCacheEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Task Scheduler Cache event."""

  DATA_TYPE = 'task_scheduler:task_cache:entry'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Task: {task_name}',
      '[Identifier: {task_identifier}]']

  FORMAT_STRING_SHORT_PIECES = [
      'Task: {task_name}']

  SOURCE_LONG = 'Task Cache'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(TaskCacheEventFormatter)
