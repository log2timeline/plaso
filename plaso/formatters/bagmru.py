# -*- coding: utf-8 -*-
"""The BagMRU event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class BagMRUEventFormatter(interface.EventFormatter):
  """Formatter for a BagMRU event."""

  DATA_TYPE = 'windows:registry:bagmru'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : BagMRU'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(BagMRUEventFormatter)
