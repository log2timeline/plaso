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
      values = '(empty)'
    elif isinstance(values, list):
      values = ' '.join([
          '{0:s}: [{1:s}] {2:s}'.format(
              name or '(default)', data_type, data or '(empty)')
          for name, data_type, data in sorted(values)])

    event_values['values'] = values


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsRegistryValuesFormatterHelper)
