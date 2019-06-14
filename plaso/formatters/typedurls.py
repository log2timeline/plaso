# -*- coding: utf-8 -*-
"""The typed URLs event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TypedURLsFormatter(interface.EventFormatter):
  """Formatter for a typed URLs event."""

  DATA_TYPE = 'windows:registry:typedurls'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : Typed URLs'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(TypedURLsFormatter)
