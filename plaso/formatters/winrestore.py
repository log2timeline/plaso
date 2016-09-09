# -*- coding: utf-8 -*-
"""The Windows Restore Point (rp.log) file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class RestorePointInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Windows Restore Point information event."""

  DATA_TYPE = u'windows:restore_point:info'

  FORMAT_STRING_PIECES = [
      u'{description}',
      u'Event type: {restore_point_event_type}',
      u'Restore point type: {restore_point_type}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{description}']

  SOURCE_LONG = u'Windows Restore Point'
  SOURCE_SHORT = u'RP'

  _RESTORE_POINT_EVENT_TYPES = {
      100: u'BEGIN_SYSTEM_CHANGE',
      101: u'END_SYSTEM_CHANGE',
      102: u'BEGIN_NESTED_SYSTEM_CHANGE',
      103: u'END_NESTED_SYSTEM_CHANGE',
  }

  _RESTORE_POINT_TYPES = {
      0: u'APPLICATION_INSTALL',
      1: u'APPLICATION_UNINSTALL',
      10: u'DEVICE_DRIVER_INSTALL',
      12: u'MODIFY_SETTINGS',
      13: u'CANCELLED_OPERATION',
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
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    restore_point_event_type = event_values.get(
        u'restore_point_event_type', None)
    if restore_point_event_type is not None:
      event_values[u'restore_point_event_type'] = (
          self._RESTORE_POINT_EVENT_TYPES.get(
              restore_point_event_type, u'UNKNOWN'))

    restore_point_type = event_values.get(u'restore_point_type', None)
    if restore_point_type is not None:
      event_values[u'restore_point_type'] = (
          self._RESTORE_POINT_EVENT_TYPES.get(restore_point_type, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(RestorePointInfoFormatter)
