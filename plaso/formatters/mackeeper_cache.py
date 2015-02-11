# -*- coding: utf-8 -*-
"""This file contains a MacKeepr Cache formatter in plaso."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacKeeperCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for MacKeeper Cache extracted events."""

  DATA_TYPE = 'mackeeper:cache'

  FORMAT_STRING_PIECES = [
      u'{description}',
      u'<{event_type}>',
      u':', u'{text}', u'[',
      u'URL: {url}',
      u'Event ID: {record_id}',
      'Room: {room}',
      u']']

  FORMAT_STRING_SHORT_PIECES = [
      u'<{event_type}>',
      u'{text}']

  SOURCE_LONG = 'MacKeeper Cache'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacKeeperCacheFormatter)
