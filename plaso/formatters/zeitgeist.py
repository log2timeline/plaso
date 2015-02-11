# -*- coding: utf-8 -*-
"""This file contains a formatter for Zeitgeist."""

from plaso.formatters import interface
from plaso.formatters import manager


class ZeitgeistEventFormatter(interface.EventFormatter):
  """The event formatter for Zeitgeist event."""

  DATA_TYPE = 'zeitgeist:activity'

  FORMAT_STRING = u'{subject_uri}'

  SOURCE_LONG = 'Zeitgeist activity log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(ZeitgeistEventFormatter)
