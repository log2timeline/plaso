# -*- coding: utf-8 -*-
"""The Windows Scheduled Task (job) event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class WinJobFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Scheduled Task (job) event."""

  DATA_TYPE = u'windows:tasks:job'

  FORMAT_STRING_PIECES = [
      u'Application: {application}',
      u'{parameter}',
      u'Scheduled by: {username}',
      u'Working Directory: {working_dir}',
      u'Run Iteration: {trigger}']

  SOURCE_LONG = u'Windows Scheduled Task Job'
  SOURCE_SHORT = u'JOB'


manager.FormattersManager.RegisterFormatter(WinJobFormatter)
