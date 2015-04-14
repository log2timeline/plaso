# -*- coding: utf-8 -*-
"""The text file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class TextEntryFormatter(interface.EventFormatter):
  """Formatter for a text file entry event."""

  DATA_TYPE = u'text:entry'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Text File'


manager.FormattersManager.RegisterFormatter(TextEntryFormatter)
