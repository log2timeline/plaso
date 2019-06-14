# -*- coding: utf-8 -*-
"""The MSIE zone settings event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MSIEZoneSettingsEventFormatter(interface.EventFormatter):
  """Formatter for a MSIE zone settings event."""

  DATA_TYPE = 'windows:registry:msie_zone_settings'

  FORMAT_STRING = '[{key_path}] {settings}'
  FORMAT_STRING_ALTERNATIVE = '{settings}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(MSIEZoneSettingsEventFormatter)
