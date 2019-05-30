# -*- coding: utf-8 -*-
"""The Run/RunOnce key event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class RunKeyEventFormatter(interface.EventFormatter):
  """Formatter for a Run/RunOnce key event."""

  DATA_TYPE = 'windows:registry:run'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : Run Key'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(RunKeyEventFormatter)
