# -*- coding: utf-8 -*-
"""The UTMPX binary file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class UtmpxSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMPX session event."""

  DATA_TYPE = 'mac:utmpx:event'

  FORMAT_STRING_PIECES = [
      'User: {user}',
      'Status: {status}',
      'Computer Name: {computer_name}',
      'Terminal: {terminal}']

  FORMAT_STRING_SHORT_PIECES = ['User: {user}']

  SOURCE_LONG = 'UTMPX session'
  SOURCE_SHORT = 'LOG'

  # 9, 10 and 11 are only for Darwin and IOS.
  _STATUS_TYPES = {
      0: 'EMPTY',
      1: 'RUN_LVL',
      2: 'BOOT_TIME',
      3: 'OLD_TIME',
      4: 'NEW_TIME',
      5: 'INIT_PROCESS',
      6: 'LOGIN_PROCESS',
      7: 'USER_PROCESS',
      8: 'DEAD_PROCESS',
      9: 'ACCOUNTING',
      10: 'SIGNATURE',
      11: 'SHUTDOWN_TIME'}

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

    status_type = event_values.get('status_type', None)
    if status_type is not None:
      event_values['status'] = self._STATUS_TYPES.get(
          status_type, '{0:d}'.format(status_type))
    else:
      event_values['status'] = 'N/A'

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(UtmpxSessionFormatter)
