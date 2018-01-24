# -*- coding: utf-8 -*-
"""The MacOS launch services (LS) quarantine event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class LSQuarantineFormatter(interface.ConditionalEventFormatter):
  """Formatter for a launch services (LS) quarantine history event."""

  DATA_TYPE = 'macosx:lsquarantine'

  FORMAT_STRING_PIECES = [
      '[{agent}]',
      'Downloaded: {url}',
      '<{data}>']

  FORMAT_STRING_SHORT_PIECES = ['{url}']

  SOURCE_LONG = 'LS Quarantine Event'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(LSQuarantineFormatter)
