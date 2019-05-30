# -*- coding: utf-8 -*-
"""The Windows Restore Point (rp.log) file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class RestorePointInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Windows Restore Point information event."""

  DATA_TYPE = 'windows:restore_point:info'

  FORMAT_STRING_PIECES = [
      '{description}',
      'Event type: {restore_point_event_type}',
      'Restore point type: {restore_point_type}']

  FORMAT_STRING_SHORT_PIECES = [
      '{description}']

  SOURCE_LONG = 'Windows Restore Point'
  SOURCE_SHORT = 'RP'

  _RESTORE_POINT_EVENT_TYPES = {
      100: 'BEGIN_SYSTEM_CHANGE',
      101: 'END_SYSTEM_CHANGE',
      102: 'BEGIN_NESTED_SYSTEM_CHANGE',
      103: 'END_NESTED_SYSTEM_CHANGE',
  }

  _RESTORE_POINT_TYPES = {
      0: 'APPLICATION_INSTALL',
      1: 'APPLICATION_UNINSTALL',
      10: 'DEVICE_DRIVER_INSTALL',
      12: 'MODIFY_SETTINGS',
      13: 'CANCELLED_OPERATION',
  }

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

    restore_point_event_type = event_values.get(
        'restore_point_event_type', None)
    if restore_point_event_type is not None:
      event_values['restore_point_event_type'] = (
          self._RESTORE_POINT_EVENT_TYPES.get(
              restore_point_event_type, 'UNKNOWN'))

    restore_point_type = event_values.get('restore_point_type', None)
    if restore_point_type is not None:
      event_values['restore_point_type'] = (
          self._RESTORE_POINT_EVENT_TYPES.get(restore_point_type, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(RestorePointInfoFormatter)
