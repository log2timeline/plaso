# -*- coding: utf-8 -*-
"""Contains a formatter for a dynamic output module for plaso."""

import logging

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class DynamicFieldsHelper(object):
  """Helper for outputting a dynamic selection of fields."""

  # A dict containing mappings between the name of fields and
  # a callback function that formats the field value.
  _FIELD_FORMAT_CALLBACKS = {
      u'date': u'_FormatDate',
      u'datetime': u'_FormatDateTime',
      u'description': u'_FormatMessage',
      u'description_short': u'_FormatMessageShort',
      u'host': u'_FormatHostname',
      u'hostname': u'_FormatHostname',
      u'inode': u'_FormatInode',
      u'macb': u'_FormatMACB',
      u'message': u'_FormatMessage',
      u'message_short': u'_FormatMessageShort',
      u'source': u'_FormatSourceShort',
      u'sourcetype': u'_FormatSource',
      u'source_long': u'_FormatSource',
      u'tag': u'_FormatTag',
      u'time': u'_FormatTime',
      u'timezone': u'_FormatZone',
      u'type': u'_FormatTimestampDescription',
      u'user': u'_FormatUsername',
      u'username': u'_FormatUsername',
      u'zone': u'_FormatZone',
  }

  def __init__(self, output_mediator):
    """Initializes a dynamic fields helper.

    Args:
      output_mediator (OutputMediator): output mediator.
    """
    super(DynamicFieldsHelper, self).__init__()
    self._output_mediator = output_mediator

  def _FormatDate(self, event):
    """Formats the date.

    Args:
      event (EventObject): event.

    Returns:
      str: date field.
    """
    try:
      date_use = timelib.Timestamp.CopyToDatetime(
          event.timestamp, self._output_mediator.timezone,
          raise_error=True)
    except OverflowError as exception:
      self._ReportEventError(event, (
          u'unable to copy timestamp: {0:d} to a human readable date '
          u'with error: {1:s}. Defaulting to: "0000-00-00"').format(
              event.timestamp, exception))

      return u'0000-00-00'

    return u'{0:04d}-{1:02d}-{2:02d}'.format(
        date_use.year, date_use.month, date_use.day)

  def _FormatDateTime(self, event):
    """Formats the date and time in ISO 8601 format.

    Args:
      event (EventObject): event.

    Returns:
      str: date and time field.
    """
    try:
      return timelib.Timestamp.CopyToIsoFormat(
          event.timestamp, timezone=self._output_mediator.timezone,
          raise_error=True)

    except OverflowError as exception:
      self._ReportEventError(event, (
          u'unable to copy timestamp: {0:d} to a human readable date and time '
          u'with error: {1:s}. Defaulting to: "0000-00-00T00:00:00"').format(
              event.timestamp, exception))

      return u'0000-00-00T00:00:00'

  def _FormatHostname(self, event):
    """Formats the hostname.

    Args:
      event (EventObject): event.

    Returns:
      str: hostname field.
    """
    return self._output_mediator.GetHostname(event)

  def _FormatInode(self, event):
    """Formats the inode.

    Args:
      event (EventObject): event.

    Returns:
      str: inode field.
    """
    inode = event.inode
    if inode is None:
      if (hasattr(event, u'pathspec') and
          hasattr(event.pathspec, u'image_inode')):
        inode = event.pathspec.image_inode
    if inode is None:
      inode = u'-'

    return inode

  def _FormatMACB(self, event):
    """Formats the legacy MACB representation.

    Args:
      event (EventObject): event.

    Returns:
      str: MACB field.
    """
    return self._output_mediator.GetMACBRepresentation(event)

  def _FormatMessage(self, event):
    """Formats the message.

    Args:
      event (EventObject): event.

    Returns:
      str: message field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event.
    """
    message, _ = self._output_mediator.GetFormattedMessages(event)
    if message is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    return message

  def _FormatMessageShort(self, event):
    """Formats the short message.

    Args:
      event (EventObject): event.

    Returns:
      str: short message field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event.
    """
    _, message_short = self._output_mediator.GetFormattedMessages(event)
    if message_short is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    return message_short

  def _FormatSource(self, event):
    """Formats the source.

    Args:
      event (EventObject): event.

    Returns:
      str: source field.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event.
    """
    _, source = self._output_mediator.GetFormattedSources(event)
    if source is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    return source

  def _FormatSourceShort(self, event):
    """Formats the short source.

    Args:
      event (EventObject): event.

    Returns:
      str: short source field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event.
    """
    source_short, _ = self._output_mediator.GetFormattedSources(event)
    if source_short is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    return source_short

  def _FormatTag(self, event):
    """Formats the event tag.

    Args:
      event (EventObject): event.

    Returns:
      str: event tag field.
    """
    tag = getattr(event, u'tag', None)

    if not tag:
      return u'-'

    return u' '.join(tag.labels)

  def _FormatTime(self, event):
    """Formats the time.

    Args:
      event (EventObject): event.

    Returns:
      str: time field.
    """
    try:
      date_use = timelib.Timestamp.CopyToDatetime(
          event.timestamp, self._output_mediator.timezone,
          raise_error=True)
    except OverflowError as exception:
      self._ReportEventError(event, (
          u'unable to copy timestamp: {0:d} to a human readable time '
          u'with error: {1:s}. Defaulting to: "00:00:00"').format(
              event.timestamp, exception))

      return u'00:00:00'

    return u'{0:02d}:{1:02d}:{2:02d}'.format(
        date_use.hour, date_use.minute, date_use.second)

  def _FormatTimestampDescription(self, event):
    """Formats the timestamp description.

    Args:
      event (EventObject): event.

    Returns:
      str: timestamp description field.
    """
    return getattr(event, u'timestamp_desc', u'-')

  def _FormatUsername(self, event):
    """Formats the username.

    Args:
      event (EventObject): event.

    Returns:
      str: username field.
    """
    return self._output_mediator.GetUsername(event)

  def _FormatZone(self, unused_event):
    """Formats the time zone.

    Args:
      event (EventObject): event.

    Returns:
      str: time zone field.
    """
    return self._output_mediator.timezone

  def _ReportEventError(self, event, error_message):
    """Reports an event related error.

    Args:
      event (EventObject): event.
      error_message (str): error message.
    """
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()
    error_message = (
        u'Event: {0!s} data type: {1:s} display name: {2:s} '
        u'parser chain: {3:s} with error: {4:s}').format(
            event_identifier_string, event.data_type, event.display_name,
            event.parser, error_message)
    logging.error(error_message)

  def GetFormattedField(self, event, field_name):
    """Formats the specified field.

    Args:
      event (EventObject): event.
      field_name (str): name of the field.

    Returns:
      str: value of the field.
    """
    callback_name = self._FIELD_FORMAT_CALLBACKS.get(field_name, None)
    callback_function = None
    if callback_name:
      callback_function = getattr(self, callback_name, None)

    if callback_function:
      output_value = callback_function(event)
    else:
      output_value = getattr(event, field_name, u'-')

    if output_value is None:
      output_value = u'-'

    elif not isinstance(output_value, py2to3.STRING_TYPES):
      output_value = u'{0!s}'.format(output_value)

    return output_value


class DynamicOutputModule(interface.LinearOutputModule):
  """Dynamic selection of fields for a separated value output format."""

  NAME = u'dynamic'
  DESCRIPTION = (
      u'Dynamic selection of fields for a separated value output format.')

  _DEFAULT_FIELD_DELIMITER = u','

  _DEFAULT_FIELDS = [
      u'datetime', u'timestamp_desc', u'source', u'source_long',
      u'message', u'parser', u'display_name', u'tag']

  def __init__(self, output_mediator):
    """Initializes an output module object.

    Args:
      output_mediator (OutputMediator): an output mediator.
    """
    super(DynamicOutputModule, self).__init__(output_mediator)
    self._dynamic_fields_helper = DynamicFieldsHelper(output_mediator)
    self._field_delimiter = self._DEFAULT_FIELD_DELIMITER
    self._fields = self._DEFAULT_FIELDS

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method replaces any field delimiters with a space.

    Args:
      field (str): name of the field to sanitize.

    Returns:
      str: value of the field.
    """
    if self._field_delimiter and isinstance(field, py2to3.STRING_TYPES):
      return field.replace(self._field_delimiter, u' ')
    return field

  def SetFieldDelimiter(self, field_delimiter):
    """Sets the field delimiter.

    Args:
      field_delimiter (str): field delimiter.
    """
    self._field_delimiter = field_delimiter

  def SetFields(self, fields):
    """Sets the fields to output.

    Args:
      fields (list[str]): names of the fields to output.
    """
    self._fields = fields

  def WriteEventBody(self, event):
    """Writes the body of an event to the output.

    Args:
      event (EventObject): event.
    """
    output_values = []
    for field_name in self._fields:
      output_value = self._dynamic_fields_helper.GetFormattedField(
          event, field_name)

      output_value = self._SanitizeField(output_value)
      output_values.append(output_value)

    output_line = u'{0:s}\n'.format(self._field_delimiter.join(output_values))
    self._WriteLine(output_line)

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(u'{0:s}\n'.format(self._field_delimiter.join(self._fields)))


manager.OutputManager.RegisterOutput(DynamicOutputModule)
