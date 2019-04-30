# -*- coding: utf-8 -*-
"""The Mac Notes zhtmlstring event formatter."""
from __future__ import unicode_literals
import re

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class MacNotesNotesFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac Notes zhtlmstring record"""

  DATA_TYPE = 'mac:notes:zhtmlstring'

  FORMAT_STRING_PIECES = [
      'note_body:{zhtmlstring}',
      'title:{title}']

  FORMAT_STRING_SHORT_PIECES = ['title:{title}']

  SOURCE_LONG = 'Mac Notes Zhtmlstring'
  SOURCE_SHORT = 'Mac Notes'

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event):
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
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    body = re.sub(
        r'(<\/?(html|head|div|body|span|b|table|tr|td|tbody|p).*>\n?)',
        '', event_values.get('zhtmlstring', None))
    event_values['zhtmlstring'] = body

    return self._ConditionalFormatMessages(event_values)

manager.FormattersManager.RegisterFormatter(MacNotesNotesFormatter)
