# -*- coding: utf-8 -*-
"""The default event formatter."""

from plaso.formatters import interface
from plaso.lib import definitions


class DefaultEventFormatter(interface.BasicEventFormatter):
  """Formatter for events that do not have any defined formatter."""

  DATA_TYPE = 'event'
  FORMAT_STRING = '<WARNING DEFAULT FORMATTER> Attributes: {attribute_driven}'
  FORMAT_STRING_SHORT = '<DEFAULT> {attribute_driven}'

  def __init__(self):
    """Initializes a default event formatter."""
    super(DefaultEventFormatter, self).__init__(
        data_type=self.DATA_TYPE, format_string=self.FORMAT_STRING,
        format_string_short=self.FORMAT_STRING_SHORT)

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    # TODO: clean up the default formatter and add a test to make sure
    # it is clear how it is intended to work.
    text_pieces = []
    for key, value in event_values.items():
      if key not in definitions.RESERVED_VARIABLE_NAMES:
        text_pieces.append('{0:s}: {1!s}'.format(key, value))

    event_values['attribute_driven'] = ' '.join(text_pieces)
    event_values['data_type'] = self.DATA_TYPE
