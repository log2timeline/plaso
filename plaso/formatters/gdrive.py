# -*- coding: utf-8 -*-
"""The Google Drive snapshots event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class GDriveCloudEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive snapshot cloud event."""

  DATA_TYPE = 'gdrive:snapshot:cloud_entry'

  FORMAT_STRING_PIECES = [
      u'File Path: {path}',
      u'[{shared}]',
      u'Size: {size}',
      u'URL: {url}',
      u'Type: {document_type}']

  FORMAT_STRING_SHORT_PIECES = [u'{path}']

  SOURCE_LONG = 'Google Drive (cloud entry)'
  SOURCE_SHORT = 'LOG'


class GDriveLocalEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive snapshot local event."""

  DATA_TYPE = 'gdrive:snapshot:local_entry'

  FORMAT_STRING_PIECES = [
      u'File Path: {path}',
      u'Size: {size}']

  FORMAT_STRING_SHORT_PIECES = [u'{path}']

  SOURCE_LONG = 'Google Drive (local entry)'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    GDriveCloudEntryFormatter, GDriveLocalEntryFormatter])
