# -*- coding: utf-8 -*-
"""The CCleaner event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class CCleanerUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a CCleaner update event."""

  DATA_TYPE = u'ccleaner:update'

  FORMAT_STRING_PIECES = [
      u'Origin: {key_path}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Origin: {key_path}']

  SOURCE_LONG = u'System'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(
    CCleanerUpdateEventFormatter)
