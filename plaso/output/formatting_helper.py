# -*- coding: utf-8 -*-
"""Output module field formatting helper."""

import abc
import csv
import datetime
import os

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.lib import errors
from plaso.lib import timelib
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
    self._source_mappings = {}

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

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
      NoFormatterFound: if no message formatter can be found to match the data
          type in the event data.
      WrongFormatter: if the event data cannot be formatted by the message
          formatter.
    """
    message_formatter = self._output_mediator.GetMessageFormatter(
        event_data.data_type)
    if not message_formatter:
      raise errors.NoFormatterFound((
          'Unable to find message formatter event with data type: '
          '{0:s}.').format(event_data.data_type))

    event_values = event_data.CopyToDict()
    message_formatter.FormatEventValues(event_values)

    if event_data.data_type in ('windows:evt:record', 'windows:evtx:record'):
      event_values['message_string'] = self._FormatWindowsEventLogMessage(
          event, event_data, event_data_stream)

    return message_formatter.GetMessage(event_values)

  def _FormatMessageShort(self, event, event_data, event_data_stream):
    """Formats a short message field.

    Args:
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
    message_formatter = self._output_mediator.GetMessageFormatter(
        event_data.data_type)
    if not message_formatter:
      raise errors.NoFormatterFound((
          'Unable to find message formatter event with data type: '
          '{0:s}.').format(event_data.data_type))

    event_values = event_data.CopyToDict()
    message_formatter.FormatEventValues(event_values)

    if event_data.data_type in ('windows:evt:record', 'windows:evtx:record'):
      event_values['message_string'] = self._FormatWindowsEventLogMessage(
          event, event_data, event_data_stream)

    return message_formatter.GetMessageShort(event_values)

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
    if not self._source_mappings:
      self._ReadSourceMappings()

    data_type = getattr(event_data, 'data_type', 'default')
    _, source = self._source_mappings.get(data_type, (None, None))
    if source is None:
      return 'N/A'

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
    if not self._source_mappings:
      self._ReadSourceMappings()

    data_type = getattr(event_data, 'data_type', None)
    source_short, _ = self._source_mappings.get(data_type, (None, None))
    if source_short is None:
      return 'N/A'

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

  def _FormatWindowsEventLogMessage(self, event, event_data, event_data_stream):
    """Formats a Windows Event Log message field.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: Windows Event Log message field or None if not available.
    """
    message_string = None
    source_name = getattr(event_data, 'source_name', None)
    message_identifier = getattr(event_data, 'message_identifier', None)
    if source_name and message_identifier:
      windows_event_message = self._output_mediator.GetWindowsEventMessage(
          source_name, message_identifier)
      if windows_event_message:
        try:
          message_string = windows_event_message.format(*event_data.strings)
        except IndexError:
          # Unable to create the message string.
          # TODO: consider returning the unformatted message string.
          pass

    return message_string

  # pylint: enable=unused-argument

  def _ReadSourceMappings(self):
    """Reads the source mappings from the sources.config data file."""
    self._source_mappings = {}

    try:
      sources_data_file = os.path.join(
          self._output_mediator.data_location, 'sources.config')

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
