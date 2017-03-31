# -*- coding: utf-8 -*-
"""The Google Drive snapshots event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


__author__ = 'David Nides (david.nides@gmail.com)'


class GDriveCloudEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive snapshot cloud event."""

  DATA_TYPE = u'gdrive:snapshot:cloud_entry'

  FORMAT_STRING_PIECES = [
      u'File Path: {path}',
      u'[{shared}]',
      u'Size: {size}',
      u'URL: {url}',
      u'Type: {document_type}']

  FORMAT_STRING_SHORT_PIECES = [u'{path}']

  SOURCE_LONG = u'Google Drive (cloud entry)'
  SOURCE_SHORT = u'LOG'

  # The following definition for values can be found on Patrick Olson's blog:
  # http://www.sysforensics.org/2012/05/google-drive-forensics-notes.html
  _DOC_TYPES = {
      0: u'FOLDER',
      1: u'FILE',
      2: u'PRESENTATION',
      3: u'UNKNOWN',
      4: u'SPREADSHEET',
      5: u'DRAWING',
      6: u'DOCUMENT',
      7: u'TABLE',
  }

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    document_type = event_values.get(u'document_type', None)
    if document_type:
      event_values[u'document_type'] = self._DOC_TYPES.get(
          document_type, u'UNKNOWN')

    shared = event_values.get(u'shared', False)
    if shared:
      event_values[u'shared'] = u'Shared'
    else:
      event_values[u'shared'] = u'Private'

    return self._ConditionalFormatMessages(event_values)


class GDriveLocalEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive snapshot local event."""

  DATA_TYPE = u'gdrive:snapshot:local_entry'

  FORMAT_STRING_PIECES = [
      u'File Path: {path}',
      u'Size: {size}']

  FORMAT_STRING_SHORT_PIECES = [u'{path}']

  SOURCE_LONG = u'Google Drive (local entry)'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatters([
    GDriveCloudEntryFormatter, GDriveLocalEntryFormatter])
