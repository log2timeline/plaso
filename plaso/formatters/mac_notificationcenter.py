# -*- coding: utf-8 -*-
"""The MacOS Notification Center event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacNotificationCenterFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS Notification Center event."""

  DATA_TYPE = 'mac:notificationcenter:db'

  FORMAT_STRING_PIECES = [
      'Notification title "{title}" ',
      '(subtitle: {subtitle},), ',
      'registered by {bundle_name}. ',
      'Delivery status "{presented}", ',
      'with the following content: "{body}"']

  FORMAT_STRING_SHORT_PIECES = [
      'Notification title "{title}"']

  SOURCE_LONG = 'Notification Center - event database'
  SOURCE_SHORT = 'Notification Center'


manager.FormattersManager.RegisterFormatter(MacNotificationCenterFormatter)
