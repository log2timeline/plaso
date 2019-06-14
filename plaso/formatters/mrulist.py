# -*- coding: utf-8 -*-
"""The MRUList event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MRUListEventFormatter(interface.EventFormatter):
  """Formatter for a MRUList event."""

  DATA_TYPE = 'windows:registry:mrulist'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : MRU List'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(MRUListEventFormatter)
