# -*- coding: utf-8 -*-
"""The plist event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class PlistFormatter(interface.ConditionalEventFormatter):
  """Formatter for a plist key event."""

  DATA_TYPE = 'plist:key'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '{root}/',
      '{key}',
      ' {desc}']

  SOURCE_LONG = 'Plist Entry'
  SOURCE_SHORT = 'PLIST'


manager.FormattersManager.RegisterFormatter(PlistFormatter)
