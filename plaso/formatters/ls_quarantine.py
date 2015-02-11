# -*- coding: utf-8 -*-
"""Formatter for the Mac OS X launch services quarantine events."""

from plaso.formatters import interface
from plaso.formatters import manager


class LSQuarantineFormatter(interface.ConditionalEventFormatter):
  """Formatter for a LS Quarantine history event."""

  DATA_TYPE = 'macosx:lsquarantine'

  FORMAT_STRING_PIECES = [
      u'[{agent}]',
      u'Downloaded: {url}',
      u'<{data}>']

  FORMAT_STRING_SHORT_PIECES = [u'{url}']

  SOURCE_LONG = 'LS Quarantine Event'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(LSQuarantineFormatter)
