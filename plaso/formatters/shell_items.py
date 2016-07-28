# -*- coding: utf-8 -*-
"""The shell item event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ShellItemFileEntryEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a shell item file entry event."""

  DATA_TYPE = u'windows:shell_item:file_entry'

  FORMAT_STRING_PIECES = [
      u'Name: {name}',
      u'Long name: {long_name}',
      u'Localized name: {localized_name}',
      u'NTFS file reference: {file_reference}',
      u'Shell item path: {shell_item_path}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Name: {file_entry_name}',
      u'NTFS file reference: {file_reference}',
      u'Origin: {origin}']

  SOURCE_LONG = u'File entry shell item'
  SOURCE_SHORT = u'FILE'

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

    event_values[u'file_entry_name'] = event_values.get(u'long_name', None)
    if not event_values[u'file_entry_name']:
      event_values[u'file_entry_name'] = event_values.get(u'name', None)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(ShellItemFileEntryEventFormatter)
