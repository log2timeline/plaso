# -*- coding: utf-8 -*-
"""The Windows Scheduled Task (job) event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    trigger_type = event_values.get('trigger_type', None)
    if trigger_type is not None:
      event_values['trigger_type'] = self._TRIGGER_TYPES.get(
          trigger_type, '0x{0:04x}'.format(trigger_type))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinJobFormatter)
