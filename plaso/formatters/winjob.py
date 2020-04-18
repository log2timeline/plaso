# -*- coding: utf-8 -*-
"""The Windows Scheduled Task (job) event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinJobFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Scheduled Task (job) event."""

  DATA_TYPE = 'windows:tasks:job'

  FORMAT_STRING_PIECES = [
      'Application: {application}',
      '{parameters}',
      'Scheduled by: {username}',
      'Working directory: {working_directory}',
      'Trigger type: {trigger_type}']

  SOURCE_LONG = 'Windows Scheduled Task Job'
  SOURCE_SHORT = 'JOB'

  _TRIGGER_TYPES = {
      0x0000: 'ONCE',
      0x0001: 'DAILY',
      0x0002: 'WEEKLY',
      0x0003: 'MONTHLYDATE',
      0x0004: 'MONTHLYDOW',
      0x0005: 'EVENT_ON_IDLE',
      0x0006: 'EVENT_AT_SYSTEMSTART',
      0x0007: 'EVENT_AT_LOGON'
  }

  def __init__(self):
    """Initializes a Windows Scheduled Task (job) event format helper."""
    super(WinJobFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='trigger_type',
        output_attribute='trigger_type', values=self._TRIGGER_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(WinJobFormatter)
