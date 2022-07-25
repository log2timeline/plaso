# -*- coding: utf-8 -*-
"""Output module field formatting helper."""

import abc
import csv
import datetime
import os
import pytz

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import events
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

  def __init__(self):
    """Initializes a field formatting helper."""
    event_data_stream = events.EventDataStream()

    super(FieldFormattingHelper, self).__init__()
    self._callback_functions = {}
    self._event_data_stream_field_names = event_data_stream.GetAttributeNames()
    self._event_tag_field_names = []
    self._source_mappings = {}
    self._winevt_resources_helper = None

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
      output_mediator (OutputMediator): output mediator.
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

      if output_mediator.timezone != pytz.UTC or date_time.time_zone_offset:
        # For output in a specific time zone overwrite the date, time in
        # seconds and time zone offset in the UTC ISO8601 string.
        year, month, day_of_month, hours, minutes, seconds = (
            date_time.GetDateWithTimeOfDay())

        try:
          datetime_object = datetime.datetime(
              year, month, day_of_month, hours, minutes, seconds,
              tzinfo=pytz.UTC)

          datetime_object = datetime_object.astimezone(output_mediator.timezone)

          isoformat_string = datetime_object.isoformat()
          iso8601_string = ''.join([
              isoformat_string[:19], iso8601_string[19:-6],
              isoformat_string[-6:]])
        except (OSError, OverflowError, TypeError, ValueError):
          return 'Invalid'

    else:
      # For now check if event.timestamp is set, to mimic existing behavior of
      # using 0000-00-00T00:00:00.000000+00:00 for 0 timestamp values
      if not output_mediator.dynamic_time and not event.timestamp:
        return '0000-00-00T00:00:00.000000+00:00'

      date_time = event.date_time
      if not date_time or date_time.is_local_time:
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=event.timestamp)

      number_of_seconds, fraction_of_second = (
          date_time.CopyToPosixTimestampWithFractionOfSecond())
      fraction_of_second = fraction_of_second or 0
      while fraction_of_second > 1000000:
        fraction_of_second, _ = divmod(fraction_of_second, 10)

      try:
        datetime_object = datetime.datetime(1970, 1, 1) + datetime.timedelta(
            seconds=number_of_seconds)

        datetime_object = datetime_object.astimezone(output_mediator.timezone)

        iso8601_string = datetime_object.isoformat()
        iso8601_string = '{0:s}.{1:06d}{2:s}'.format(
            iso8601_string[:19], fraction_of_second, iso8601_string[-6:])

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
      output_mediator (OutputMediator): output mediator.
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
      output_mediator (OutputMediator): output mediator.
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
        filename = output_mediator.GetRelativePathForPathSpec(path_spec)
      else:
        filename = '-'

    return filename

  def _FormatHostname(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a hostname field.

    Args:
      output_mediator (OutputMediator): output mediator.
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
      output_mediator (OutputMediator): output mediator.
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
      output_mediator (OutputMediator): output mediator.
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
      output_mediator (OutputMediator): output mediator.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: message field.

    Raises:
      NoFormatterFound: if no message formatter can be found to match the data
          type in the event data.
      WrongFormatter: if the event data cannot be formatted by the message
          formatter.
    """
    message_formatter = output_mediator.GetMessageFormatter(
        event_data.data_type)
    if not message_formatter:
      raise errors.NoFormatterFound((
          'Unable to find message formatter event with data type: '
          '{0:s}.').format(event_data.data_type))

    event_values = event_data.CopyToDict()
    message_formatter.FormatEventValues(event_values)

    if event_data.data_type in ('windows:evt:record', 'windows:evtx:record'):
      event_values['message_string'] = self._FormatWindowsEventLogMessage(
          output_mediator, event, event_data, event_data_stream)

    return message_formatter.GetMessage(event_values)

  def _FormatMessageShort(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a short message field.

    Args:
      output_mediator (OutputMediator): output mediator.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: short message field.

    Raises:
      NoFormatterFound: if no message formatter can be found to match the data
          type in the event data.
      WrongFormatter: if the event data cannot be formatted by the message
          formatter.
    """
    message_formatter = output_mediator.GetMessageFormatter(
        event_data.data_type)
    if not message_formatter:
      raise errors.NoFormatterFound((
          'Unable to find message formatter event with data type: '
          '{0:s}.').format(event_data.data_type))

    event_values = event_data.CopyToDict()
    message_formatter.FormatEventValues(event_values)

    if event_data.data_type in ('windows:evt:record', 'windows:evtx:record'):
      event_values['message_string'] = self._FormatWindowsEventLogMessage(
          output_mediator, event, event_data, event_data_stream)

    return message_formatter.GetMessageShort(event_values)

  def _FormatSource(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a source field.

    Args:
      output_mediator (OutputMediator): output mediator.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: source field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event data.
    """
    if not self._source_mappings:
      self._ReadSourceMappings(output_mediator)

    data_type = getattr(event_data, 'data_type', 'default')
    _, source = self._source_mappings.get(data_type, (None, None))
    if source is None:
      return 'N/A'

    return source

  def _FormatSourceShort(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a short source field.

    Args:
      output_mediator (OutputMediator): output mediator.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: short source field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event data.
    """
    if not self._source_mappings:
      self._ReadSourceMappings(output_mediator)

    data_type = getattr(event_data, 'data_type', None)
    source_short, _ = self._source_mappings.get(data_type, (None, None))
    if source_short is None:
      return 'N/A'

    return source_short

  def _FormatTag(self, output_mediator, event_tag):
    """Formats an event tag field.

    Args:
      output_mediator (OutputMediator): output mediator.
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
      output_mediator (OutputMediator): output mediator.
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

    if output_mediator.timezone != pytz.UTC:
      try:
        datetime_object = datetime.datetime(
            year, month, day_of_month, hours, minutes, seconds,
            tzinfo=pytz.UTC)

        datetime_object = datetime_object.astimezone(output_mediator.timezone)

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
      output_mediator (OutputMediator): output mediator.
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

    if output_mediator.timezone == pytz.UTC:
      return 'UTC'

    year, month, day_of_month, hours, minutes, seconds = (
        date_time.GetDateWithTimeOfDay())

    try:
      # For tzname to work the datetime object must be naive (without
      # a time zone).
      datetime_object = datetime.datetime(
          year, month, day_of_month, hours, minutes, seconds)
      return output_mediator.timezone.tzname(datetime_object)

    except (OverflowError, TypeError, ValueError):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable time zone. '
          'Defaulting to: "-"').format(event.timestamp))

      return '-'

  def _FormatUsername(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats an username field.

    Args:
      output_mediator (OutputMediator): output mediator.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: username field.
    """
    return output_mediator.GetUsername(event_data)

  def _FormatWindowsEventLogMessage(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a Windows Event Log message field.

    Args:
      output_mediator (OutputMediator): output mediator.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: Windows Event Log message field or None if not available.
    """
    if not self._winevt_resources_helper:
      self._winevt_resources_helper = output_mediator.GetWinevtResourcesHelper()

    message_string = None
    provider_identifier = getattr(event_data, 'provider_identifier', None)
    source_name = getattr(event_data, 'source_name', None)
    message_identifier = getattr(event_data, 'message_identifier', None)
    event_version = getattr(event_data, 'event_version', None)
    if (provider_identifier or source_name) and message_identifier:
      message_string_template = self._winevt_resources_helper.GetMessageString(
          provider_identifier, source_name, message_identifier, event_version)
      if message_string_template:
        string_values = [string or '' for string in event_data.strings]
        try:
          message_string = message_string_template.format(*string_values)
        except (IndexError, TypeError) as exception:
          logger.error((
              'Unable to format message string: "{0:s}" and strings: "{1:s}" '
              'with error: {2!s}').format(
                  message_string_template, ', '.join(string_values), exception))
          # Unable to create the message string.
          # TODO: consider returning the unformatted message string.

    return message_string

  # pylint: enable=unused-argument

  # TODO: move to mediator.
  def _ReadSourceMappings(self, output_mediator):
    """Reads the source mappings from the sources.config data file.

    Args:
      output_mediator (OutputMediator): output mediator.
    """
    self._source_mappings = {}

    try:
      sources_data_file = os.path.join(
          output_mediator.data_location, 'sources.config')

      with open(sources_data_file, encoding='utf8') as file_object:
        csv_reader = csv.reader(file_object, delimiter='\t')
        # Note that csv.reader returns a list per row.
        header_row = next(csv_reader)
        if header_row == ['data_type', 'short_source', 'source']:
          for row in csv_reader:
            try:
              self._source_mappings[row[0]] = (row[1], row[2])
            except IndexError:
              logger.error('Invalid source mapping: {0!s}'.format(row))

    except (IOError, TypeError, csv.Error):
      pass

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
      output_mediator (OutputMediator): output mediator.
      field_name (str): name of the field.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: value of the field.
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

    if output_value is None:
      output_value = '-'

    elif not isinstance(output_value, str):
      output_value = '{0!s}'.format(output_value)

    return output_value
