# -*- coding: utf-8 -*-
"""The Zeitgeist event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ZeitgeistFormatter(interface.EventFormatter):
  """Formatter for a Zeitgeist activity database event."""

  DATA_TYPE = 'zeitgeist:activity'

  FORMAT_STRING = '{subject_uri}'

  SOURCE_LONG = 'Zeitgeist activity log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(ZeitgeistFormatter)
