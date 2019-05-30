# -*- coding: utf-8 -*-
"""The CCleaner event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class CCleanerConfigurationEventFormatter(interface.EventFormatter):
  """Formatter for a CCleaner configuration event."""

  DATA_TYPE = 'ccleaner:configuration'

  FORMAT_STRING = '[{key_path}] {configuration}'
  FORMAT_STRING_ALTERNATIVE = '{configuration}'

  SOURCE_LONG = 'Registry Key : CCleaner Registry key'
  SOURCE_SHORT = 'REG'


class CCleanerUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a CCleaner update event."""

  DATA_TYPE = 'ccleaner:update'

  FORMAT_STRING_PIECES = [
      'Origin: {key_path}']

  FORMAT_STRING_SHORT_PIECES = [
      'Origin: {key_path}']

  SOURCE_LONG = 'System'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    CCleanerConfigurationEventFormatter,
    CCleanerUpdateEventFormatter])
