# -*- coding: utf-8 -*-
"""The Google Drive snapshots event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class GDriveCloudEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive snapshot cloud event."""

  DATA_TYPE = 'gdrive:snapshot:cloud_entry'

  FORMAT_STRING_PIECES = [
      'File Path: {path}',
      '[{shared}]',
      'Size: {size}',
      'URL: {url}',
      'Type: {document_type}']

  FORMAT_STRING_SHORT_PIECES = ['{path}']

  SOURCE_LONG = 'Google Drive (cloud entry)'
  SOURCE_SHORT = 'LOG'

  # The following definition for values can be found on Patrick Olson's blog:
  # http://www.sysforensics.org/2012/05/google-drive-forensics-notes.html
  _DOC_TYPES = {
      0: 'FOLDER',
      1: 'FILE',
      2: 'PRESENTATION',
      3: 'UNKNOWN',
      4: 'SPREADSHEET',
      5: 'DRAWING',
      6: 'DOCUMENT',
      7: 'TABLE',
  }

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    document_type = event_values.get('document_type', None)
    if document_type:
      event_values['document_type'] = self._DOC_TYPES.get(
          document_type, 'UNKNOWN')

    shared = event_values.get('shared', False)
    if shared:
      event_values['shared'] = 'Shared'
    else:
      event_values['shared'] = 'Private'

    return self._ConditionalFormatMessages(event_values)


class GDriveLocalEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive snapshot local event."""

  DATA_TYPE = 'gdrive:snapshot:local_entry'

  FORMAT_STRING_PIECES = [
      'File Path: {path}',
      'Size: {size}']

  FORMAT_STRING_SHORT_PIECES = ['{path}']

  SOURCE_LONG = 'Google Drive (local entry)'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    GDriveCloudEntryFormatter, GDriveLocalEntryFormatter])
