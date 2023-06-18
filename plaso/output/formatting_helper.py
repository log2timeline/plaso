# -*- coding: utf-8 -*-
"""Output module field formatting helper."""

import abc
import datetime
import math
import pytz

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import events
from plaso.formatters import default
from plaso.output import logger


class EventFormattingHelper(object):
  """Output module event formatting helper."""

  @abc.abstractmethod
  def GetFieldValues(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves the output field values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      list[str]: output field values.
    """


class FieldFormattingHelper(object):
  """Output module field formatting helper."""

  _DEFAULT_MESSAGE_FORMATTER = default.DefaultEventFormatter()

  # Maps the name of a field to callback function that formats the field value.
  _FIELD_FORMAT_CALLBACKS = {}

  def __init__(self):
    """Initializes a field formatting helper."""
    event_data_stream = events.EventDataStream()

    super(FieldFormattingHelper, self).__init__()
    self._callback_functions = {}
    self._event_data_stream_field_names = event_data_stream.GetAttributeNames()
    self._event_tag_field_names = []

    for field_name, callback_name in self._FIELD_FORMAT_CALLBACKS.items():
      if callback_name == '_FormatTag':
        self._event_tag_field_names.append(field_name)
      else:
        self._callback_functions[field_name] = getattr(
            self, callback_name, None)

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

  def _FormatDateTime(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a date and time field in ISO 8601 format.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date and time field with time zone offset, semantic time.
    """
    if output_mediator.dynamic_time and event.date_time:
      iso8601_string = getattr(event.date_time, 'string', None)
      if iso8601_string:
        return iso8601_string

      date_time = event.date_time
      if event.date_time.is_local_time:
        # TODO: replace this by a more generic solution.
        if event.date_time.precision == '1s':
          timestamp, _ = divmod(event.timestamp, 1000000)
          date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        else:
          date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
              timestamp=event.timestamp)

      iso8601_string = date_time.CopyToDateTimeStringISO8601()
      if not iso8601_string:
        return 'Invalid'

      if iso8601_string[-1] == 'Z':
        iso8601_string = '{0:s}+00:00'.format(iso8601_string[:-1])

      if output_mediator.time_zone != pytz.UTC or date_time.time_zone_offset:
        # For output in a specific time zone overwrite the date, time in
        # seconds and time zone offset in the UTC ISO8601 string.
        year, month, day_of_month, hours, minutes, seconds = (
            date_time.GetDateWithTimeOfDay())

        try:
          datetime_object = datetime.datetime(
              year, month, day_of_month, hours, minutes, seconds,
              tzinfo=pytz.UTC)

          datetime_object = datetime_object.astimezone(
              output_mediator.time_zone)

          isoformat_string = datetime_object.isoformat()
          iso8601_string = ''.join([
              isoformat_string[:19], iso8601_string[19:-6],
              isoformat_string[-6:]])
        except (OSError, OverflowError, TypeError, ValueError):
          return 'Invalid'

    else:
      if not event.date_time or event.date_time.is_local_time:
        timestamp = event.timestamp
      else:
        timestamp, fraction_of_second = (
            event.date_time.CopyToPosixTimestampWithFractionOfSecond())

        fraction_of_second = (fraction_of_second or 0) * 100000
        while fraction_of_second <= -1000000 or fraction_of_second >= 1000000:
          fraction_of_second /= 10

        timestamp = (timestamp or 0) * 1000000
        if fraction_of_second < 0:
          timestamp += math.floor(fraction_of_second)
        else:
          timestamp += math.ceil(fraction_of_second)

      # For now check if event.timestamp is set, to mimic existing behavior of
      # using 0000-00-00T00:00:00.000000+00:00 for 0 timestamp values
      if not timestamp:
        return '0000-00-00T00:00:00.000000+00:00'

      try:
        datetime_object = datetime.datetime(1970, 1, 1) + datetime.timedelta(
            microseconds=timestamp)

        datetime_object = datetime_object.astimezone(output_mediator.time_zone)

        iso8601_string = datetime_object.isoformat()
        iso8601_string = '{0:s}.{1:06d}{2:s}'.format(
            iso8601_string[:19], datetime_object.microsecond,
            iso8601_string[-6:])

      except (OSError, OverflowError, TypeError, ValueError) as exception:
        iso8601_string = '0000-00-00T00:00:00.000000+00:00'
        self._ReportEventError(event, event_data, (
            'unable to copy timestamp: {0!s} to a human readable date and '
            'time with error: {1!s}. Defaulting to: "{2:s}"').format(
                event.timestamp, exception, iso8601_string))

    return iso8601_string

  def _FormatDisplayName(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats the display name.

    The display_name field can be set as an attribute to event_data otherwise
    it is derived from the path specification.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date field.
    """
    display_name = getattr(event_data, 'display_name', None)
    if not display_name:
      path_spec = getattr(event_data_stream, 'path_spec', None)
      if path_spec:
        display_name = output_mediator.GetDisplayNameForPathSpec(path_spec)
      else:
        display_name = '-'

    return display_name

  def _FormatFilename(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats the filename.

    The filename field can be set as an attribute to event_data otherwise
    it is derived from the path specification.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: date field.
    """
    filename = getattr(event_data, 'filename', None)
    if not filename:
      path_spec = getattr(event_data_stream, 'path_spec', None)
      if path_spec:
        filename = output_mediator.GetRelativePathForPathSpec(path_spec)
      else:
        filename = '-'

    return filename

  def _FormatHostname(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a hostname field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: hostname field.
    """
    return output_mediator.GetHostname(event_data)

  def _FormatInode(self, output_mediator, event, event_data, event_data_stream):
    """Formats an inode field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
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
      if path_specification:
        if path_specification.type_indicator in (
            dfvfs_definitions.TYPE_INDICATOR_APFS,
            dfvfs_definitions.TYPE_INDICATOR_HFS):
          inode = getattr(path_specification, 'identifier', None)

        elif path_specification.type_indicator == (
            dfvfs_definitions.TYPE_INDICATOR_NTFS):
          inode = getattr(path_specification, 'mft_entry', None)

        elif path_specification.type_indicator in (
            dfvfs_definitions.TYPE_INDICATOR_EXT,
            dfvfs_definitions.TYPE_INDICATOR_TSK):
          # Note that inode can contain a TSK metadata address.
          inode = getattr(path_specification, 'inode', None)

    if inode is None:
      inode = '-'

    elif isinstance(inode, int):
      inode = '{0:d}'.format(inode)

    return inode

  def _FormatMACB(self, output_mediator, event, event_data, event_data_stream):
    """Formats a legacy MACB representation field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: MACB field.
    """
    return output_mediator.GetMACBRepresentation(event, event_data)

  def _FormatMessage(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a message field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: message field.
    """
    message_formatter = output_mediator.GetMessageFormatter(
        event_data.data_type)
    if not message_formatter:
      logger.warning(
          'Using default message formatter for data type: {0:s}'.format(
              event_data.data_type))
      message_formatter = self._DEFAULT_MESSAGE_FORMATTER

    event_values = event_data.CopyToDict()
    message_formatter.FormatEventValues(output_mediator, event_values)

    return message_formatter.GetMessage(event_values)

  def _FormatMessageShort(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a short message field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: short message field.
    """
    message_formatter = output_mediator.GetMessageFormatter(
        event_data.data_type)
    if not message_formatter:
      logger.warning(
          'Using default message formatter for data type: {0:s}'.format(
              event_data.data_type))
      message_formatter = self._DEFAULT_MESSAGE_FORMATTER

    event_values = event_data.CopyToDict()
    message_formatter.FormatEventValues(output_mediator, event_values)

    return message_formatter.GetMessageShort(event_values)

  def _FormatSource(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a source field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: source field.
    """
    data_type = getattr(event_data, 'data_type', None) or '-'
    _, source = output_mediator.GetSourceMapping(data_type)
    return source or 'N/A'

  def _FormatSourceShort(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a short source field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: short source field.
    """
    data_type = getattr(event_data, 'data_type', None) or '-'
    source_short, _ = output_mediator.GetSourceMapping(data_type)
    return source_short or 'N/A'

  def _FormatTag(self, output_mediator, event_tag):
    """Formats an event tag field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event_tag (EventTag): event tag or None if not set.

    Returns:
      str: event tag labels or "-" if event tag is not set.
    """
    if not event_tag:
      return '-'

    return ' '.join(event_tag.labels)

  def _FormatTime(self, output_mediator, event, event_data, event_data_stream):
    """Formats a time field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: time in seconds formatted as "HH:MM:SS" or "--:--:--" on error.
    """
    # For now check if event.timestamp is set, to mimic existing behavior of
    # using --:--:-- for 0 timestamp values.
    if not event.timestamp:
      return '--:--:--'

    date_time = event.date_time
    if not date_time or date_time.is_local_time:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=event.timestamp)

    year, month, day_of_month, hours, minutes, seconds = (
        date_time.GetDateWithTimeOfDay())

    if output_mediator.time_zone != pytz.UTC:
      try:
        datetime_object = datetime.datetime(
            year, month, day_of_month, hours, minutes, seconds,
            tzinfo=pytz.UTC)

        datetime_object = datetime_object.astimezone(output_mediator.time_zone)

        hours, minutes, seconds = (
            datetime_object.hour, datetime_object.minute,
            datetime_object.second)

      except (OSError, OverflowError, TypeError, ValueError):
        hours, minutes, seconds = (None, None, None)

    if None in (hours, minutes, seconds):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable time. '
          'Defaulting to: "--:--:--"').format(event.timestamp))
      return '--:--:--'

    return '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)

  def _FormatTimeZone(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a time zone field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: time zone field.
    """
    if not event.timestamp:
      return '-'

    date_time = event.date_time
    if not date_time or date_time.is_local_time:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=event.timestamp)

    if output_mediator.time_zone == pytz.UTC:
      return 'UTC'

    year, month, day_of_month, hours, minutes, seconds = (
        date_time.GetDateWithTimeOfDay())

    try:
      # For tzname to work the datetime object must be naive (without
      # a time zone).
      datetime_object = datetime.datetime(
          year, month, day_of_month, hours, minutes, seconds)
      return output_mediator.time_zone.tzname(datetime_object)

    except (OverflowError, TypeError, ValueError):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable time zone. '
          'Defaulting to: "-"').format(event.timestamp))

      return '-'

  def _FormatUsername(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats an username field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: username field.
    """
    return output_mediator.GetUsername(event_data)

  def _FormatValues(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: values field.
    """
    values = event_data.values
    if isinstance(values, list) and event_data.data_type in (
        'windows:registry:key_value', 'windows:registry:service'):
      values = ' '.join([
          '{0:s}: [{1:s}] {2:s}'.format(
              name or '(default)', data_type, data or '(empty)')
          for name, data_type, data in sorted(values)])

    return values

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

    parser_chain = getattr(event_data, '_parser_chain', None)
    if not parser_chain:
      # Note that parser is kept for backwards compatibility.
      parser_chain = getattr(event_data, 'parser', None) or 'N/A'

    error_message = (
        'Event: {0!s} description: {1:s} data type: {2:s} display name: {3:s} '
        'parser chain: {4:s} with error: {5:s}').format(
            event_identifier_string, event.timestamp_desc, event_data.data_type,
            display_name, parser_chain, error_message)
    logger.error(error_message)

  def GetFormattedField(
      self, output_mediator, field_name, event, event_data, event_data_stream,
      event_tag):
    """Formats the specified field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_name (str): name of the field.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: value of the field or None if not available.
    """
    if field_name in self._event_tag_field_names:
      return self._FormatTag(output_mediator, event_tag)

    callback_function = self._callback_functions.get(field_name, None)
    if callback_function:
      output_value = callback_function(
          output_mediator, event, event_data, event_data_stream)
    elif field_name in self._event_data_stream_field_names:
      output_value = getattr(event_data_stream, field_name, None)
    else:
      output_value = getattr(event_data, field_name, None)

    if output_value is not None and not isinstance(output_value, str):
      output_value = '{0!s}'.format(output_value)

    return output_value
