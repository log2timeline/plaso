# -*- coding: utf-8 -*-
"""The MacOS Notification Center event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacNotificationCenterFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS Notification Center event."""

  DATA_TYPE = 'mac:notificationcenter:db'

  FORMAT_STRING_PIECES = [
      'Title: {title}',
      '(, subtitle: {subtitle}),',
      'registered by: {bundle_name}.',
      'Presented: {presented},',
      'Content: {body}']

  FORMAT_STRING_SHORT_PIECES = [
      'Title: {title},',
      'Content: {body}']

  SOURCE_LONG = 'Notification Center'
  SOURCE_SHORT = 'NOTIFICATION'

  _PRESENTED_VALUES = {
      0: 'No',
      1: 'Yes'
  }

  def __init__(self):
    """Initializes an a MacOS Notification Center event format helper."""
    super(MacNotificationCenterFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='presented',
        output_attribute='presented', values=self._PRESENTED_VALUES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(MacNotificationCenterFormatter)
