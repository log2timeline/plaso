# -*- coding: utf-8 -*-
"""The shutdown Windows Registry event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ShutdownWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a shutdown Windows Registry event."""

  DATA_TYPE = u'windows:registry:shutdown'

  FORMAT_STRING_PIECES = [
      u'[{key_path}]',
      u'Description: {value_name}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{value_name}']

  SOURCE_LONG = u'Registry Key Shutdown Entry'
  SOURCE_SHORT = u'REG'

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

    regvalue = event_values.get(u'regvalue', {})
    string_parts = []
    for key, value in sorted(regvalue.items()):
      string_parts.append(u'{0:s}: {1!s}'.format(key, value))
    event_values[u'text'] = u' '.join(string_parts)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(
    ShutdownWindowsRegistryEventFormatter)
