# -*- coding: utf-8 -*-
"""The Windows Restore Point (rp.log) file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class RestorePointInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Restore Point information event."""

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

  def __init__(self):
    """Initializes a Windows Restore Point information event format helper."""
    super(RestorePointInfoFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='restore_point_event_type',
        output_attribute='restore_point_event_type',
        values=self._RESTORE_POINT_EVENT_TYPES)

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='restore_point_type',
        output_attribute='restore_point_type', values=self._RESTORE_POINT_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(RestorePointInfoFormatter)
