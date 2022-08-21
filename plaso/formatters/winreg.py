# -*- coding: utf-8 -*-
"""Windows Registry custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsRegistryValuesFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Windows Registry values formatter helper."""

  IDENTIFIER = 'windows_registry_values'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    values = event_values.get('values', None)
    if not values:
      event_values['values'] = '(empty)'


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsRegistryValuesFormatterHelper)
