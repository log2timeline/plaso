# -*- coding: utf-8 -*-
"""The shell item event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ShellItemFileEntryEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a shell item file entry event."""

  DATA_TYPE = 'windows:shell_item:file_entry'

  FORMAT_STRING_PIECES = [
      'Name: {name}',
      'Long name: {long_name}',
      'Localized name: {localized_name}',
      'NTFS file reference: {file_reference}',
      'Shell item path: {shell_item_path}',
      'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      'Name: {file_entry_name}',
      'NTFS file reference: {file_reference}',
      'Origin: {origin}']

  SOURCE_LONG = 'File entry shell item'
  SOURCE_SHORT = 'FILE'

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

    event_values['file_entry_name'] = event_values.get('long_name', None)
    if not event_values['file_entry_name']:
      event_values['file_entry_name'] = event_values.get('name', None)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(ShellItemFileEntryEventFormatter)
