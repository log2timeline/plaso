# -*- coding: utf-8 -*-
"""The Zsh extended_history formatter."""
from plaso.formatters import interface
from plaso.formatters import manager


class ZshExtendedHistoryEventFormatter(interface.ConditionalEventFormatter):
  """Class for the Zsh event formatter."""

  DATA_TYPE = u'shell:zsh:history'

  FORMAT_STRING_SEPARATOR = u' '

  FORMAT_STRING_PIECES = [
      u'{command}',
      u'Time elapsed: {elapsed_seconds} seconds']

  FORMAT_STRING_SHORT_PIECES = [u'{command}']

  SOURCE_LONG = u'Zsh Extended History'
  SOURCE_SHORT = u'HIST'


manager.FormattersManager.RegisterFormatter(ZshExtendedHistoryEventFormatter)
