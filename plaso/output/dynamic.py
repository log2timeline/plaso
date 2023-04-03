# -*- coding: utf-8 -*-
"""Dynamic selected delimiter separated values output module."""

import datetime
import pytz

from dfdatetime import posix_time as dfdatetime_posix_time

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
      'values': '_FormatValues',
      'yara_match': '_FormatYaraMatch',
      'zone': '_FormatTimeZone'}

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

  def _FormatDate(self, output_mediator, event, event_data, event_data_stream):
    """Formats a date field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date formatted as "YYYY-MM-DD" or "0000-00-00" on error.
    """
    # For now check if event.timestamp is set, to mimic existing behavior of
    # using 0000-00-00 for 0 timestamp values.
    if not event.timestamp:
      return '0000-00-00'

    date_time = event.date_time
    if not date_time or date_time.is_local_time:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=event.timestamp)

    # Note that GetDateWithTimeOfDay will return the date and time in UTC,
    # so no adjustment for date_time.time_zone_offset is needed.
    year, month, day_of_month, hours, minutes, seconds = (
        date_time.GetDateWithTimeOfDay())

    if output_mediator.time_zone != pytz.UTC:
      try:
        datetime_object = datetime.datetime(
            year, month, day_of_month, hours, minutes, seconds,
            tzinfo=pytz.UTC)

        datetime_object = datetime_object.astimezone(output_mediator.time_zone)

        year = datetime_object.year
        month = datetime_object.month
        day_of_month = datetime_object.day

      except (OSError, OverflowError, TypeError, ValueError):
        year, month, day_of_month = (None, None, None)

    if None in (year, month, day_of_month):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date. '
          'Defaulting to: "0000-00-00"').format(event.timestamp))
      return '0000-00-00'

    return '{0:04d}-{1:02d}-{2:02d}'.format(year, month, day_of_month)

  def _FormatTimestampDescription(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a timestamp description field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: timestamp description field.
    """
    return event.timestamp_desc or '-'

  def _FormatYaraMatch(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a Yara match field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: Yara match field.
    """
    yara_match = getattr(event_data_stream, 'yara_match', None) or []
    return '; '.join(yara_match) or '-'

  # pylint: enable=unused-argument


class DynamicOutputModule(shared_dsv.DSVOutputModule):
  """Dynamic selected delimiter separated values (DSV) output module."""

  NAME = 'dynamic'
  DESCRIPTION = (
      'Dynamic selection of fields for a separated value output format.')

  SUPPORTS_ADDITIONAL_FIELDS = True
  SUPPORTS_CUSTOM_FIELDS = True

  _DEFAULT_NAMES = [
      'datetime', 'timestamp_desc', 'source', 'source_long', 'message',
      'parser', 'display_name', 'tag']

  _SORT_KEY_FIELD_NAMES = ['datetime', 'display_name', 'message']

  def __init__(self):
    """Initializes an output module."""
    field_formatting_helper = DynamicFieldFormattingHelper()
    super(DynamicOutputModule, self).__init__(
        field_formatting_helper, self._DEFAULT_NAMES)


manager.OutputManager.RegisterOutput(DynamicOutputModule)
