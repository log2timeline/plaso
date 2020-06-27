# -*- coding: utf-8 -*-
"""Output module field formatting helper."""

from __future__ import unicode_literals

import abc
import datetime

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.lib import errors
from plaso.output import logger


class EventFormattingHelper(object):
  """Output module event formatting helper."""

  def __init__(self, output_mediator):
    """Initializes an event formatting helper.

    Args:
      output_mediator (OutputMediator): output mediator.
    """
    super(EventFormattingHelper, self).__init__()
    self._output_mediator = output_mediator

  @abc.abstractmethod
  def GetFormattedEvent(self, event, event_data, event_data_stream, event_tag):
    """Retrieves a string representation of the event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: string representation of the event.
    """


class FieldFormattingHelper(object):
  """Output module field formatting helper."""

  # Maps the name of a field to callback function that formats the field value.
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

    # Note that inode can contain 0.
    if inode is None:
      path_specification = getattr(event_data_stream, 'path_spec', None)
      if not path_specification:
        # Note that support for event_data.pathspec is kept for backwards
        # compatibility.
        path_specification = getattr(event_data, 'pathspec', None)

      if path_specification:
        if path_specification.type_indicator == (
            dfvfs_definitions.TYPE_INDICATOR_APFS):
          inode = getattr(path_specification, 'identifier', None)

        elif path_specification.type_indicator == (
            dfvfs_definitions.TYPE_INDICATOR_NTFS):
          inode = getattr(path_specification, 'mft_entry', None)

        elif path_specification.type_indicator == (
            dfvfs_definitions.TYPE_INDICATOR_TSK):
          # Note that inode contains the TSK metadata address.
          inode = getattr(path_specification, 'inode', None)

    if inode is None:
      inode = '-'

    elif isinstance(inode, int):
      inode = '{0:d}'.format(inode)

    return inode

  def _FormatMACB(self, event, event_data, event_data_stream):
    """Formats a legacy MACB representation field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: MACB field.
    """
    return self._output_mediator.GetMACBRepresentation(event, event_data)

  def _FormatMessage(self, event, event_data, event_data_stream):
    """Formats a message field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: message field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event data.
    """
    # TODO: refactor GetFormattedMessages by GetFormattedMessage.
    message, _ = self._output_mediator.GetFormattedMessages(event_data)
    if message is None:
      raise errors.NoFormatterFound(
          'Unable to create message for event with data type: {0:s}.'.format(
              event_data.data_type))

    return message

  def _FormatMessageShort(self, event, event_data, event_data_stream):
    """Formats a short message field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: short message field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event data.
    """
    # TODO: refactor GetFormattedMessages by GetFormattedMessageShort.
    _, message_short = self._output_mediator.GetFormattedMessages(event_data)
    if message_short is None:
      raise errors.NoFormatterFound(
          'Unable to create message for event with data type: {0:s}.'.format(
              event_data.data_type))

    return message_short

  def _FormatSource(self, event, event_data, event_data_stream):
    """Formats a source field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: source field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event data.
    """
    # TODO: refactor GetFormattedSources by GetFormattedSource.
    _, source = self._output_mediator.GetFormattedSources(event, event_data)
    if source is None:
      raise errors.NoFormatterFound(
          'Unable to create source for event with data type: {0:s}.'.format(
              event_data.data_type))

    return source

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
    # TODO: refactor GetFormattedSources by GetFormattedSourceShort.
    source_short, _ = self._output_mediator.GetFormattedSources(
        event, event_data)
    if source_short is None:
      raise errors.NoFormatterFound(
          'Unable to create source for event with data type: {0:s}.'.format(
              event_data.data_type))

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
    # For tzname to work the datetime object must be naive (without a time
    # zone).
    try:
      datetime_object = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)
      datetime_object += datetime.timedelta(microseconds=event.timestamp)
      return self._output_mediator.timezone.tzname(datetime_object)

    except OverflowError:
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable time zone. '
          'Defaulting to: "00/00/0000"').format(event.timestamp))

      return '-'

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

  def _ReportEventError(self, event, event_data, error_message):
    """Reports an event related error.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      error_message (str): error message.
    """
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()
    display_name = getattr(event_data, 'display_name', None) or 'N/A'
    parser_chain = getattr(event_data, 'parser', None) or 'N/A'
    error_message = (
        'Event: {0!s} data type: {1:s} display name: {2:s} '
        'parser chain: {3:s} with error: {4:s}').format(
            event_identifier_string, event_data.data_type, display_name,
            parser_chain, error_message)
    logger.error(error_message)

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
    callback_name = self._FIELD_FORMAT_CALLBACKS.get(field_name, None)
    if callback_name == '_FormatTag':
      return self._FormatTag(event_tag)

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
