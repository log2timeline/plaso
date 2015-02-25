# -*- coding: utf-8 -*-
"""Formatter for Windows NT Registry (REGF) files."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinRegistryGenericFormatter(interface.EventFormatter):
  """Formatter for a generic Windows Registry key or value."""

  DATA_TYPE = 'windows:registry:key_value'

  FORMAT_STRING = u'[{keyname}] {text}'
  FORMAT_STRING_ALTERNATIVE = u'{text}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    regvalue = event_values.get(u'regvalue', {})
    string_parts = []
    for key, value in sorted(regvalue.items()):
      string_parts.append(u'{0:s}: {1!s}'.format(key, value))
    text = u' '.join(string_parts)

    event_values[u'text'] = text
    if u'keyname' in event_values:
      format_string = self.FORMAT_STRING
    else:
      format_string = self.FORMAT_STRING_ALTERNATIVE

    return self._FormatMessages(
        format_string, self.FORMAT_STRING_SHORT, event_values)

  def GetSources(self, event_object):
    """Determines the the short and long source for an event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple of the short and long source string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    source_long = getattr(event_object, u'source_long', None)
    if not source_long:
      registry_type = getattr(event_object, u'registry_type', u'UNKNOWN')
      source_long = u'{0:s} key'.format(registry_type)

    if hasattr(event_object, u'source_append'):
      source_long += u' {0:s}'.format(event_object.source_append)

    return self.SOURCE_SHORT, source_long


manager.FormattersManager.RegisterFormatter(WinRegistryGenericFormatter)
