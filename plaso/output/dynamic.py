# -*- coding: utf-8 -*-
"""Dynamic selected delimiter separated values output module."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import formatting_helper
from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_dsv


class DynamicFieldFormattingHelper(formatting_helper.FieldFormattingHelper):
  """Dynamic output module field formatting helper."""

  # TODO: determine why _FormatTimestampDescription is mapped to both
  # timestamp_desc and type.

  # Maps the name of a fields to a a callback function that formats
  # the field value.
  _FIELD_FORMAT_CALLBACKS = {
      'date': '_FormatDate',
      'datetime': '_FormatDateTime',
      'description': '_FormatMessage',
      'description_short': '_FormatMessageShort',
      'host': '_FormatHostname',
      'hostname': '_FormatHostname',
      'inode': '_FormatInode',
      'macb': '_FormatMACB',
      'message': '_FormatMessage',
      'message_short': '_FormatMessageShort',
      'source': '_FormatSourceShort',
      'sourcetype': '_FormatSource',
      'source_long': '_FormatSource',
      'tag': '_FormatTag',
      'time': '_FormatTime',
      'timestamp_desc': '_FormatTimestampDescription',
      'timezone': '_FormatTimeZone',
      'type': '_FormatTimestampDescription',
      'user': '_FormatUsername',
      'username': '_FormatUsername',
      'zone': '_FormatTimeZone'}

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

  def _FormatDate(self, event, event_data, event_data_stream):
    """Formats a date field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date field.
    """
    try:
      iso_date_time = timelib.Timestamp.CopyToIsoFormat(
          event.timestamp, timezone=self._output_mediator.timezone,
          raise_error=True)

      return iso_date_time[:10]

    except (OverflowError, ValueError):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date. '
          'Defaulting to: "0000-00-00"').format(event.timestamp))

      return '0000-00-00'

  def _FormatDateTime(self, event, event_data, event_data_stream):
    """Formats a date and time field in ISO 8601 format.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date and time field.
    """
    try:
      return timelib.Timestamp.CopyToIsoFormat(
          event.timestamp, timezone=self._output_mediator.timezone,
          raise_error=True)

    except (OverflowError, ValueError) as exception:
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date and time '
          'with error: {1!s}. Defaulting to: "0000-00-00T00:00:00"').format(
              event.timestamp, exception))

      return '0000-00-00T00:00:00'

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
    message, _ = self._output_mediator.GetFormattedMessages(event_data)
    if message is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to create message for event with data type: {0:s}.'.format(
              data_type))

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
    _, message_short = self._output_mediator.GetFormattedMessages(event_data)
    if message_short is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to create message for event with data type: {0:s}.'.format(
              data_type))

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
    _, source = self._output_mediator.GetFormattedSources(event, event_data)
    if source is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to create source for event with data type: {0:s}.'.format(
              data_type))

    return source

  def _FormatTime(self, event, event_data, event_data_stream):
    """Formats a time field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: time field.
    """
    try:
      iso_date_time = timelib.Timestamp.CopyToIsoFormat(
          event.timestamp, timezone=self._output_mediator.timezone,
          raise_error=True)

      return iso_date_time[11:19]

    except (OverflowError, ValueError):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable time. '
          'Defaulting to: "--:--:--"').format(event.timestamp))

      return '--:--:--'

  def _FormatTimestampDescription(self, event, event_data, event_data_stream):
    """Formats a timestamp description field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: timestamp description field.
    """
    return event.timestamp_desc or '-'

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


class DynamicOutputModule(shared_dsv.DSVOutputModule):
  """Dynamic selected delimiter separated values output module."""

  NAME = 'dynamic'
  DESCRIPTION = (
      'Dynamic selection of fields for a separated value output format.')

  _DEFAULT_NAMES = [
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag']

  def __init__(self, output_mediator):
    """Initializes an output module object.

    Args:
      output_mediator (OutputMediator): an output mediator.
    """
    formatting_helper_object = DynamicFieldFormattingHelper(output_mediator)
    super(DynamicOutputModule, self).__init__(
        output_mediator, formatting_helper_object, self._DEFAULT_NAMES)


manager.OutputManager.RegisterOutput(DynamicOutputModule)
