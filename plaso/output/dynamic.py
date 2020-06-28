# -*- coding: utf-8 -*-
"""Dynamic selected delimiter separated values output module."""

from __future__ import unicode_literals

from plaso.lib import timelib
from plaso.output import formatting_helper
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
      'display_name': '_FormatDisplayName',
      'filename': '_FormatFilename',
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

  def _FormatDisplayName(self, event, event_data, event_data_stream):
    """Formats the display name.

    The display_name field can be set as an attribute to event_data otherwise
    it is derived from the path specificiation.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date field.
    """
    display_name = getattr(event_data, 'display_name', None)
    if not display_name:
      path_spec = getattr(event_data_stream, 'path_spec', None)
      if not path_spec:
        path_spec = getattr(event_data, 'pathspec', None)

      if path_spec:
        display_name = self._output_mediator.GetDisplayNameForPathSpec(
            path_spec)
      else:
        display_name = '-'

    return display_name

  def _FormatFilename(self, event, event_data, event_data_stream):
    """Formats the filename.

    The filename field can be set as an attribute to event_data otherwise
    it is derived from the path specificiation.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date field.
    """
    filename = getattr(event_data, 'filename', None)
    if not filename:
      path_spec = getattr(event_data_stream, 'path_spec', None)
      if not path_spec:
        path_spec = getattr(event_data, 'pathspec', None)

      if path_spec:
        filename = self._output_mediator.GetRelativePathForPathSpec(path_spec)
      else:
        filename = '-'

    return filename

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


class DynamicOutputModule(shared_dsv.DSVOutputModule):
  """Dynamic selected delimiter separated values output module."""

  NAME = 'dynamic'
  DESCRIPTION = (
      'Dynamic selection of fields for a separated value output format.')

  _DEFAULT_NAMES = [
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag']

  def __init__(self, output_mediator):
    """Initializes a dynamic delimiter separated values output module object.

    Args:
      output_mediator (OutputMediator): an output mediator.
    """
    field_formatting_helper = DynamicFieldFormattingHelper(output_mediator)
    super(DynamicOutputModule, self).__init__(
        output_mediator, field_formatting_helper, self._DEFAULT_NAMES)


manager.OutputManager.RegisterOutput(DynamicOutputModule)
