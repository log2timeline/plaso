# -*- coding: utf-8 -*-
"""The MacKeeper Cache event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacKeeperCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacKeeper Cache event."""

  DATA_TYPE = 'mackeeper:cache'

  FORMAT_STRING_PIECES = [
      '{description}',
      '<{event_type}>',
      ':',
      '{text}',
      '[',
      'URL: {url}',
      'Event ID: {record_id}',
      'Room: {room}',
      ']']

  FORMAT_STRING_SHORT_PIECES = [
      '<{event_type}>',
      '{text}']

  SOURCE_LONG = 'MacKeeper Cache'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacKeeperCacheFormatter)
