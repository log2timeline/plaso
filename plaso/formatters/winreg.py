# -*- coding: utf-8 -*-
"""The Windows Registry key or value event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinRegistryGenericFormatter(interface.EventFormatter):
  """Formatter for a Windows Registry key or value event."""

  DATA_TYPE = 'windows:registry:key_value'

  FORMAT_STRING = '[{key_path}] {text}'
  FORMAT_STRING_ALTERNATIVE = '{text}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    regvalue = event_values.get('regvalue', {})
    string_parts = []
    for key, value in sorted(regvalue.items()):
      string_parts.append('{0:s}: {1!s}'.format(key, value))
    event_values['text'] = ' '.join(string_parts)

    urls = event_values.get('urls', [])
    if urls:
      event_values['urls'] = ' - '.join(urls)

    if 'key_path' in event_values:
      format_string = self.FORMAT_STRING
    else:
      format_string = self.FORMAT_STRING_ALTERNATIVE

    return self._FormatMessages(
        format_string, self.FORMAT_STRING_SHORT, event_values)

  def GetSources(self, event):
    """Determines the the short and long source for an event object.

    Args:
      event (EventObject): event.

    Returns:
      tuple(str, str): short and long source string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event.data_type))

    source_long = getattr(event, 'source_long', 'UNKNOWN')
    source_append = getattr(event, 'source_append', None)
    if source_append:
      source_long = '{0:s} {1:s}'.format(source_long, source_append)

    return self.SOURCE_SHORT, source_long


manager.FormattersManager.RegisterFormatter(WinRegistryGenericFormatter)
