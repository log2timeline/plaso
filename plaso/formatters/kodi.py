# -*- coding: utf-8 -*-
"""The Kodi MyVideos database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class KodiFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Kodi Video event."""

  DATA_TYPE = 'kodi:videos:viewing'

  FORMAT_STRING_PIECES = [
      'Video: {FileName}']

  FORMAT_STRING_SHORT_PIECES = ['{FileName}']

  SOURCE_LONG = 'Kodi Video Viewed'
  SOURCE_SHORT = 'KODI'


manager.FormattersManager.RegisterFormatter(KodiFormatter)
