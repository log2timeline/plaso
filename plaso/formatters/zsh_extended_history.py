# -*- coding: utf-8 -*-
"""The Zsh extended_history formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ZshExtendedHistoryEventFormatter(interface.ConditionalEventFormatter):
  """Class for the Zsh event formatter."""

  DATA_TYPE = 'shell:zsh:history'

  FORMAT_STRING_SEPARATOR = ' '

  FORMAT_STRING_PIECES = [
      '{command}',
      'Time elapsed: {elapsed_seconds} seconds']

  FORMAT_STRING_SHORT_PIECES = ['{command}']

  SOURCE_LONG = 'Zsh Extended History'
  SOURCE_SHORT = 'HIST'


manager.FormattersManager.RegisterFormatter(ZshExtendedHistoryEventFormatter)
