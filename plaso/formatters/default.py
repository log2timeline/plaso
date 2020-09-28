# -*- coding: utf-8 -*-
"""The default event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.lib import definitions


class DefaultFormatter(interface.EventFormatter):
  """Formatter for events that do not have any defined formatter."""

  DATA_TYPE = 'event'
  FORMAT_STRING = '<WARNING DEFAULT FORMATTER> Attributes: {attribute_driven}'
  FORMAT_STRING_SHORT = '<DEFAULT> {attribute_driven}'

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
    """
    event_values = event_data.CopyToDict()

    # TODO: clean up the default formatter and add a test to make sure
    # it is clear how it is intended to work.
    text_pieces = []
    for key, value in event_values.items():
      if key in definitions.RESERVED_VARIABLE_NAMES:
        continue
      text_pieces.append('{0:s}: {1!s}'.format(key, value))

    event_values['attribute_driven'] = ' '.join(text_pieces)
    event_values['data_type'] = self.DATA_TYPE

    return self._FormatMessages(
        self.FORMAT_STRING, self.FORMAT_STRING_SHORT, event_values)
