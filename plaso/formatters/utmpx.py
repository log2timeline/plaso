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
      'User: {username}',
      'Status: {status}',
      'Hostname: {hostname}',
      'Terminal: {terminal}',
      'PID: {pid}',
      'Terminal identifier: {terminal_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'User: {username}',
      'PID: {pid}',
      'Status: {status}']

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

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    login_type = event_values.get('type', None)
    if login_type is None:
      status = 'N/A'
    else:
      status = self._STATUS_TYPES.get(login_type, 'UNKNOWN')

    event_values['status'] = status

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(UtmpxSessionFormatter)
