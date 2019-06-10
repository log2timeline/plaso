# -*- coding: utf-8 -*-
"""The shutdown Windows Registry event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ShutdownWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a shutdown Windows Registry event."""

  DATA_TYPE = 'windows:registry:shutdown'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Description: {value_name}']

  FORMAT_STRING_SHORT_PIECES = [
      '{value_name}']

  SOURCE_LONG = 'Registry Key Shutdown Entry'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    ShutdownWindowsRegistryEventFormatter)
