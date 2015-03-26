# -*- coding: utf-8 -*-
"""Formatter for Windows Scheduled Task job events."""

from plaso.formatters import interface
from plaso.formatters import manager


class WinJobFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Java Cache IDX download item."""

  DATA_TYPE = 'windows:tasks:job'

  FORMAT_STRING_PIECES = [
      u'Application: {application}',
      u'{parameter}',
      u'Scheduled by: {username}',
      u'Working Directory: {working_dir}',
      u'Run Iteration: {trigger}']

  SOURCE_LONG = 'Windows Scheduled Task Job'
  SOURCE_SHORT = 'JOB'


manager.FormattersManager.RegisterFormatter(WinJobFormatter)
