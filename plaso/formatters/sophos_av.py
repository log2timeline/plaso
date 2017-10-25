# -*- coding: utf-8 -*-
"""The Sophos Anti-Virus log (SAV.txt) file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SophosAVLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Sophos Anti-Virus log (SAV.txt) event data."""

  DATA_TYPE = 'sophos:av:log'

  FORMAT_STRING_PIECES = [
      '{text}']

  SOURCE_LONG = 'Sophos Anti-Virus log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SophosAVLogFormatter)
