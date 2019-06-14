# -*- coding: utf-8 -*-
"""The Windows timezone settings event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsTimezoneSettingsEventFormatter(interface.EventFormatter):
  """Formatter for a Windows timezone settings event."""

  DATA_TYPE = 'windows:registry:timezone'

  FORMAT_STRING = '[{key_path}] {configuration}'
  FORMAT_STRING_ALTERNATIVE = '{configuration}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    WindowsTimezoneSettingsEventFormatter)
