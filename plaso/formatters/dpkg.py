# -*- coding: utf-8 -*-
"""The dpkg.log event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class DpkgFormatter(interface.ConditionalEventFormatter):
  """Formatter for a dpkg log file event."""

  DATA_TYPE = u'dpkg:line'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'{body}']

  SOURCE_LONG = u'dpkg log File'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(DpkgFormatter)
