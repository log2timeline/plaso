# -*- coding: utf-8 -*-
"""The default event formatter."""

from acstore.containers import interface as containers_interface

from dfdatetime import interface as dfdatetime_interface

from plaso.formatters import interface


class DefaultEventFormatter(interface.BasicEventFormatter):
  """Formatter for events that do not have any defined formatter."""

  DATA_TYPE = 'event'
  FORMAT_STRING = '<WARNING DEFAULT FORMATTER> Attributes: {attribute_values}'
  FORMAT_STRING_SHORT = '<DEFAULT> {attribute_values}'

  # TODO: remove attributes that are no longer considered reserved.
  _RESERVED_VARIABLE_NAMES = frozenset([
      '_event_values_hash',
      '_parser_chain',
      'body',
      'data_type',
      'display_name',
      'filename',
      'hostname',
      'http_headers',
      'inode',
      'mapped_files',
      'metadata',
      'offset',
      'parser',
      'pathspec',
      'query',
      'source_long',
      'source_short',
      'tag',
      'timestamp',
      'timestamp_desc',
      'timezone',
      'username'])

  def __init__(self):
    """Initializes a default event formatter."""
    super(DefaultEventFormatter, self).__init__(
        data_type=self.DATA_TYPE, format_string=self.FORMAT_STRING,
        format_string_short=self.FORMAT_STRING_SHORT)

  def _FormatMessage(self, format_string, event_values):
    """Determines the formatted message.

    Args:
      format_string (str): message format string.
      event_values (dict[str, object]): event values.

    Returns:
      str: formatted message.
    """
    text_pieces = []
    for name, value in event_values.items():
      # Ignore reserved variable names.
      if name in self._RESERVED_VARIABLE_NAMES:
        continue

      # Ignore attribute container identifier values.
      if isinstance(value, containers_interface.AttributeContainerIdentifier):
        continue

      # Ignore date and time values.
      if isinstance(value, dfdatetime_interface.DateTimeValues):
        continue

      if (isinstance(value, list) and value and
          isinstance(value[0], dfdatetime_interface.DateTimeValues)):
        continue

      text_pieces.append('{0:s}: {1!s}'.format(name, value))

    return super(DefaultEventFormatter, self)._FormatMessage(
        format_string, {'attribute_values': ' '.join(text_pieces)})
