# -*- coding: utf-8 -*-
"""Formatter for text file-based events."""

from plaso.formatters import interface
from plaso.formatters import manager


class TextEventFormatter(interface.EventFormatter):
  """Text event formatter."""

  DATA_TYPE = u'text:entry'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Text File'


manager.FormattersManager.RegisterFormatter(TextEventFormatter)
