# -*- coding: utf-8 -*-
"""The Hachoir event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


__author__ = 'David Nides (david.nides@gmail.com)'


class HachoirFormatter(interface.EventFormatter):
  """Formatter for a Hachoir event."""

  DATA_TYPE = u'metadata:hachoir'
  FORMAT_STRING = u'{data}'

  SOURCE_LONG = u'Hachoir Metadata'
  SOURCE_SHORT = u'META'

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

    string_parts = []
    metadata = event_values.get(u'metadata', None)
    if metadata:
      for key, value in sorted(metadata.items()):
        string_parts.append(u'{0:s}: {1:s}'.format(key, value))
    event_values[u'data'] = u' '.join(string_parts)

    return self._FormatMessages(
        self.FORMAT_STRING, self.FORMAT_STRING_SHORT, event_values)


manager.FormattersManager.RegisterFormatter(HachoirFormatter)
