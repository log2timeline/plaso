# -*- coding: utf-8 -*-
"""The dpkg.log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class DpkgFormatter(interface.ConditionalEventFormatter):
  """Formatter for a dpkg log file event."""

  DATA_TYPE = 'dpkg:line'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '{body}']

  SOURCE_LONG = 'dpkg log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(DpkgFormatter)
