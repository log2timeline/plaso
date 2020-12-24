# -*- coding: utf-8 -*-
"""The shell item event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


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

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    event_values['file_entry_name'] = event_values.get('long_name', None)
    if not event_values['file_entry_name']:
      event_values['file_entry_name'] = event_values.get('name', None)


manager.FormattersManager.RegisterFormatter(ShellItemFileEntryEventFormatter)
