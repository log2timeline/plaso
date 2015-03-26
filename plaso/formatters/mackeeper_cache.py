# -*- coding: utf-8 -*-
"""The MacKeeper Cache event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacKeeperCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacKeeper Cache event."""

  DATA_TYPE = 'mackeeper:cache'

  FORMAT_STRING_PIECES = [
      u'{description}',
      u'<{event_type}>',
      u':',
      u'{text}',
      u'[',
      u'URL: {url}',
      u'Event ID: {record_id}',
      u'Room: {room}',
      u']']

  FORMAT_STRING_SHORT_PIECES = [
      u'<{event_type}>',
      u'{text}']

  SOURCE_LONG = 'MacKeeper Cache'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacKeeperCacheFormatter)
