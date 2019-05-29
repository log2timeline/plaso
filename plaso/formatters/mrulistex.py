# -*- coding: utf-8 -*-
"""The MRUListEx event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MRUListExEventFormatter(interface.EventFormatter):
  """Formatter for a MRUListEx event."""

  DATA_TYPE = 'windows:registry:mrulistex'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : MRUListEx'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(MRUListExEventFormatter)
