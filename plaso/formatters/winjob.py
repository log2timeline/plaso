# -*- coding: utf-8 -*-
"""The Windows Scheduled Task (job) event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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

  _TRIGGER_TYPES = {
      0x0000: u'ONCE',
      0x0001: u'DAILY',
      0x0002: u'WEEKLY',
      0x0003: u'MONTHLYDATE',
      0x0004: u'MONTHLYDOW',
      0x0005: u'EVENT_ON_IDLE',
      0x0006: u'EVENT_AT_SYSTEMSTART',
      0x0007: u'EVENT_AT_LOGON'
  }

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()

    trigger = event_values.get(u'trigger', None)
    if trigger is not None:
      event_values[u'trigger'] = self._TRIGGER_TYPES.get(
          trigger, u'0x{0:04x}'.format(trigger))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinJobFormatter)
