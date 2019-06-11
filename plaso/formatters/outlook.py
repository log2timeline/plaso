# -*- coding: utf-8 -*-
"""The Outlook search MRU event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class OutlookSearchMRUEventFormatter(interface.EventFormatter):
  """Formatter for a Outlook search MRU event."""

  DATA_TYPE = 'windows:registry:outlook_search_mru'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : PST Paths'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(OutlookSearchMRUEventFormatter)
