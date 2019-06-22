# -*- coding: utf-8 -*-
"""The Windows Registry key or value event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinRegistryGenericFormatter(interface.EventFormatter):
  """Formatter for a Windows Registry key or value event."""

  DATA_TYPE = 'windows:registry:key_value'

  FORMAT_STRING = '[{key_path}] {values}'
  FORMAT_STRING_ALTERNATIVE = '{values}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'

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

    values = event_values.get('values', None)
    if values is None:
      # TODO: remove regvalue, which is kept for backwards compatibility.
      regvalue = event_values.get('regvalue', {})
      string_parts = []
      for key, value in sorted(regvalue.items()):
        string_parts.append('{0:s}: {1!s}'.format(key, value))
      values = ' '.join(string_parts)
      event_values['values'] = values

    if not values:
      event_values['values'] = '(empty)'

    if 'key_path' in event_values:
      format_string = self.FORMAT_STRING
    else:
      format_string = self.FORMAT_STRING_ALTERNATIVE

    return self._FormatMessages(
        format_string, self.FORMAT_STRING_SHORT, event_values)

  # pylint: disable=unused-argument
  def GetSources(self, event, event_data):
    """Determines the the short and long source for an event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): short and long source string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    source_long = getattr(event_data, 'source_long', 'UNKNOWN')

    # TODO: remove source_append, which is kept for backwards compatibility.
    source_append = getattr(event_data, 'source_append', None)
    if source_append:
      source_long = '{0:s} {1:s}'.format(source_long, source_append)

    return self.SOURCE_SHORT, source_long


manager.FormattersManager.RegisterFormatter(WinRegistryGenericFormatter)
