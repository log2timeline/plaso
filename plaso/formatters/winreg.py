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

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    regvalue = getattr(event_object, 'regvalue', {})

    string_parts = []
    for key, value in sorted(regvalue.items()):
      string_parts.append(u'{0:s}: {1!s}'.format(key, value))

    text = u' '.join(string_parts)

    event_object.text = text
    if hasattr(event_object, 'keyname'):
      format_string = self.FORMAT_STRING
    else:
      format_string = self.FORMAT_STRING_ALTERNATIVE

    event_values = event_object.GetValues()
    return self._FormatMessages(
        format_string, self.FORMAT_STRING_SHORT, event_values)

  def GetSources(self, event_object):
    """Returns a list of source short and long messages for the event."""
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    self.source_string = getattr(event_object, 'source_long', None)

    if not self.source_string:
      registry_type = getattr(event_object, 'registry_type', 'UNKNOWN')
      self.source_string = u'{0:s} key'.format(registry_type)

    if hasattr(event_object, 'source_append'):
      self.source_string += u' {0:s}'.format(event_object.source_append)

    return super(WinRegistryGenericFormatter, self).GetSources(event_object)


manager.FormattersManager.RegisterFormatter(WinRegistryGenericFormatter)
