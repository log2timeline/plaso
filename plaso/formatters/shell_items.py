# -*- coding: utf-8 -*-
"""Windows shell item custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class ShellItemFileEntryNameFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Windows shell item file entry formatter helper."""

  IDENTIFIER = 'shell_item_file_entry_name'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    event_values['file_entry_name'] = event_values.get('long_name', None)
    if not event_values['file_entry_name']:
      event_values['file_entry_name'] = event_values.get('name', None)


manager.FormattersManager.RegisterEventFormatterHelper(
    ShellItemFileEntryNameFormatterHelper)
