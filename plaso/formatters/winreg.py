# -*- coding: utf-8 -*-
"""Windows Registry custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinRegistryGenericFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for Windows Registry key or value event values."""

  DATA_TYPE = 'windows:registry:key_value'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    values = event_values.get('values', None)
    if not values:
      event_values['values'] = '(empty)'


manager.FormattersManager.RegisterEventFormatterHelper(
    WinRegistryGenericFormatter)
