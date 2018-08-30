# -*- coding: utf-8 -*-
"""The shutdown Windows Registry event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ShutdownWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a shutdown Windows Registry event."""

  DATA_TYPE = 'windows:registry:shutdown'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Description: {value_name}']

  FORMAT_STRING_SHORT_PIECES = [
      '{value_name}']

  SOURCE_LONG = 'Registry Key Shutdown Entry'
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

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(
    ShutdownWindowsRegistryEventFormatter)
