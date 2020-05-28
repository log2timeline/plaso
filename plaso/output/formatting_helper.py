# -*- coding: utf-8 -*-
"""Output module field formatting helper."""

from __future__ import unicode_literals

from plaso.lib import errors


class FieldFormattingHelper(object):
  """Output module field formatting helper."""

  # Maps the name of a fields to a a callback function that formats
  # the field value.
  _FIELD_FORMAT_CALLBACKS = {}

  def __init__(self, output_mediator):
    """Initializes a field formatting helper.

    Args:
      output_mediator (OutputMediator): output mediator.
    """
    super(FieldFormattingHelper, self).__init__()
    self._output_mediator = output_mediator

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

  def _FormatHostname(self, event, event_data, event_data_stream):
    """Formats a hostname field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: hostname field.
    """
    return self._output_mediator.GetHostname(event_data)

  def _FormatInode(self, event, event_data, event_data_stream):
    """Formats an inode field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: inode field.
    """
    inode = getattr(event_data, 'inode', None)
    if inode is None:
      path_specification = getattr(event_data_stream, 'path_spec', None)
      if not path_specification:
        # Note that support for event_data.pathspec is kept for backwards
        # compatibility.
        path_specification = getattr(event_data, 'pathspec', None)

      inode = getattr(path_specification, 'inode', None)

    if inode is None:
      inode = '-'

    return inode

  def _FormatSourceShort(self, event, event_data, event_data_stream):
    """Formats a short source field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: short source field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event data.
    """
    source_short, _ = self._output_mediator.GetFormattedSources(
        event, event_data)
    if source_short is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to create source for event with data type: {0:s}.'.format(
              data_type))

    return source_short

  def _FormatTag(self, event_tag):
    """Formats an event tag field.

    Args:
      event_tag (EventTag): event tag or None if not set.

    Returns:
      str: event tag labels or "-" if event tag is not set.
    """
    if not event_tag:
      return '-'

    return ' '.join(event_tag.labels)

  def _FormatTimeZone(self, event, event_data, event_data_stream):
    """Formats a time zone field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: time zone field.
    """
    return '{0!s}'.format(self._output_mediator.timezone)

  def _FormatUsername(self, event, event_data, event_data_stream):
    """Formats an username field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: username field.
    """
    return self._output_mediator.GetUsername(event_data)

  # pylint: enable=unused-argument

  def GetFormattedField(
      self, field_name, event, event_data, event_data_stream, event_tag):
    """Formats the specified field.

    Args:
      field_name (str): name of the field.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: value of the field.
    """
    if field_name == 'tag':
      return self._FormatTag(event_tag)

    callback_name = self._FIELD_FORMAT_CALLBACKS.get(field_name, None)
    callback_function = None
    if callback_name:
      callback_function = getattr(self, callback_name, None)

    if callback_function:
      output_value = callback_function(event, event_data, event_data_stream)
    elif hasattr(event_data_stream, field_name):
      output_value = getattr(event_data_stream, field_name, None)
    else:
      output_value = getattr(event_data, field_name, None)

    if output_value is None:
      output_value = '-'

    elif not isinstance(output_value, str):
      output_value = '{0!s}'.format(output_value)

    return output_value
