# -*- coding: utf-8 -*-
"""The Mac OS X launch services (LS) quarantine event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class LSQuarantineFormatter(interface.ConditionalEventFormatter):
  """Formatter for a launch services (LS) quarantine history event."""

  DATA_TYPE = u'macosx:lsquarantine'

  FORMAT_STRING_PIECES = [
      u'[{agent}]',
      u'Downloaded: {url}',
      u'<{data}>']

  FORMAT_STRING_SHORT_PIECES = [u'{url}']

  SOURCE_LONG = u'LS Quarantine Event'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(LSQuarantineFormatter)
