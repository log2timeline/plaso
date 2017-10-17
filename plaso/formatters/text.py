# -*- coding: utf-8 -*-
"""The text file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TextEntryFormatter(interface.EventFormatter):
  """Formatter for a text file entry event."""

  DATA_TYPE = 'text:entry'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Text File'


manager.FormattersManager.RegisterFormatter(TextEntryFormatter)
