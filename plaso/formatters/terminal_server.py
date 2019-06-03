# -*- coding: utf-8 -*-
"""The Terminal Server client event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TerminalServerClientConnectionEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Terminal Server client connection event."""

  DATA_TYPE = 'windows:registry:mstsc:connection'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Username hint: {username}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]']

  SOURCE_LONG = 'Registry Key : RDP Connection'
  SOURCE_SHORT = 'REG'


class TerminalServerClientMRUEventFormatter(interface.EventFormatter):
  """Formatter for a Terminal Server client MRU event."""

  DATA_TYPE = 'windows:registry:mstsc:mru'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : RDP Connection'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatters([
    TerminalServerClientConnectionEventFormatter,
    TerminalServerClientMRUEventFormatter])
