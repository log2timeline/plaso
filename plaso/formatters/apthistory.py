# -*- coding: utf-8 -*-
"""Advanced Packaging Tool (APT) History log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AptHistoryLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for an APT History log file event."""

  DATA_TYPE = 'apthistory:log:line'

  FORMAT_STRING_PIECES = [
      '{packages}',
      '{error}',
      '{requestor}']

  FORMAT_STRING_SHORT_PIECES = ['{packages}']

  SOURCE_LONG = 'APT History Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(AptHistoryLogFormatter)
