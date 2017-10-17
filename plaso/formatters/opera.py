# -*- coding: utf-8 -*-
"""The Opera history event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class OperaGlobalHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Opera global history event."""

  DATA_TYPE = 'opera:history:entry'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({title})',
      '[{description}]']

  SOURCE_LONG = 'Opera Browser History'
  SOURCE_SHORT = 'WEBHIST'


class OperaTypedHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Opera typed history event."""

  DATA_TYPE = 'opera:history:typed_entry'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({entry_selection})']

  SOURCE_LONG = 'Opera Browser History'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    OperaGlobalHistoryFormatter, OperaTypedHistoryFormatter])
