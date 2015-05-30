# -*- coding: utf-8 -*-
"""The Opera history event formatters."""

from plaso.formatters import interface
from plaso.formatters import manager


class OperaGlobalHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Opera global history event."""

  DATA_TYPE = u'opera:history:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({title})',
      u'[{description}]']

  SOURCE_LONG = u'Opera Browser History'
  SOURCE_SHORT = u'WEBHIST'


class OperaTypedHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Opera typed history event."""

  DATA_TYPE = u'opera:history:typed_entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({entry_selection})']

  SOURCE_LONG = u'Opera Browser History'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    OperaGlobalHistoryFormatter, OperaTypedHistoryFormatter])
