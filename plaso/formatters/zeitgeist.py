# -*- coding: utf-8 -*-
"""The Zeitgeist event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class ZeitgeistFormatter(interface.EventFormatter):
  """Formatter for a Zeitgeist activity database event."""

  DATA_TYPE = u'zeitgeist:activity'

  FORMAT_STRING = u'{subject_uri}'

  SOURCE_LONG = u'Zeitgeist activity log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(ZeitgeistFormatter)
