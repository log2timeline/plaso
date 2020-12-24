# -*- coding: utf-8 -*-
"""The Windows Registry key or value event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinRegistryGenericFormatter(interface.EventFormatter):
  """Formatter for a Windows Registry key or value event."""

  DATA_TYPE = 'windows:registry:key_value'

  FORMAT_STRING = '[{key_path}] {values}'
  FORMAT_STRING_ALTERNATIVE = '{values}'

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    values = event_values.get('values', None)
    if not values:
      event_values['values'] = '(empty)'

  def GetMessage(self, event_values):
    """Determines the message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: message.
    """
    if 'key_path' in event_values:
      format_string = self.FORMAT_STRING
    else:
      format_string = self.FORMAT_STRING_ALTERNATIVE

    return self._FormatMessage(format_string, event_values)

  def GetMessageShort(self, event_values):
    """Determines the short message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: short message.
    """
    if self.FORMAT_STRING_SHORT:
      format_string = self.FORMAT_STRING_SHORT
    elif 'key_path' in event_values:
      format_string = self.FORMAT_STRING
    else:
      format_string = self.FORMAT_STRING_ALTERNATIVE

    short_message_string = self._FormatMessage(format_string, event_values)

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = '{0:s}...'.format(short_message_string[:77])

    return short_message_string


manager.FormattersManager.RegisterFormatter(WinRegistryGenericFormatter)
