# -*- coding: utf-8 -*-
"""The UTMPX binary file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class UtmpxSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMPX session event."""

  DATA_TYPE = u'mac:utmpx:event'

  FORMAT_STRING_PIECES = [
      u'User: {user}',
      u'Status: {status}',
      u'Computer Name: {computer_name}',
      u'Terminal: {terminal}']

  FORMAT_STRING_SHORT_PIECES = [u'User: {user}']

  SOURCE_LONG = u'UTMPX session'
  SOURCE_SHORT = u'LOG'

  # 9, 10 and 11 are only for Darwin and IOS.
  _STATUS_TYPES = {
      0: u'EMPTY',
      1: u'RUN_LVL',
      2: u'BOOT_TIME',
      3: u'OLD_TIME',
      4: u'NEW_TIME',
      5: u'INIT_PROCESS',
      6: u'LOGIN_PROCESS',
      7: u'USER_PROCESS',
      8: u'DEAD_PROCESS',
      9: u'ACCOUNTING',
      10: u'SIGNATURE',
      11: u'SHUTDOWN_TIME'}

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

    event_values = event_object.GetValues()

    status_type = event_values.get(u'status_type', None)
    if status_type is not None:
      event_values[u'status'] = self._STATUS_TYPES.get(
          status_type, u'{0:d}'.format(status_type))
    else:
      event_values[u'status'] = u'N/A'

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(UtmpxSessionFormatter)
