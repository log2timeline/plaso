# -*- coding: utf-8 -*-
"""The default event formatter."""

from plaso.formatters import interface
from plaso.lib import definitions


class DefaultFormatter(interface.EventFormatter):
  """Default formatter for events that do not have any defined formatter."""

  DATA_TYPE = u'event'
  FORMAT_STRING = u'<WARNING DEFAULT FORMATTER> Attributes: {attribute_driven}'
  FORMAT_STRING_SHORT = u'<DEFAULT> {attribute_driven}'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.
    """
    event_values = event_object.GetValues()

    # TODO: clean up the default formatter and add a test to make sure
    # it is clear how it is intended to work.
    text_pieces = []
    for key, value in event_values.items():
      if key in definitions.RESERVED_VARIABLE_NAMES:
        continue
      text_pieces.append(u'{0:s}: {1!s}'.format(key, value))

    event_values[u'attribute_driven'] = u' '.join(text_pieces)
    event_values[u'data_type'] = self.DATA_TYPE

    return self._FormatMessages(
        self.FORMAT_STRING, self.FORMAT_STRING_SHORT, event_values)
