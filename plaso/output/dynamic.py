# -*- coding: utf-8 -*-
"""Contains a formatter for a dynamic output module for plaso."""

import logging
import re

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class DynamicOutputModule(interface.LinearOutputModule):
  """Dynamic selection of fields for a separated value output format."""

  NAME = u'dynamic'
  DESCRIPTION = (
      u'Dynamic selection of fields for a separated value output format.')

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  # TODO: Evaluate which fields should be included by default.
  _DEFAULT_FIELDS = [
      u'datetime', u'timestamp_desc', u'source', u'source_long',
      u'message', u'parser', u'display_name', u'tag', u'store_number',
      u'store_index']

  _FIELD_DELIMITER = u','

  # A dict containing mappings between the name of fields and
  # a callback function that formats the field value.
  # They should be documented here:
  #   http://plaso.kiddaland.net/usage/psort/output
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
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(DynamicOutputModule, self).__init__(output_mediator)
    self._field_delimiter = self._FIELD_DELIMITER
    self._fields = self._DEFAULT_FIELDS

  def _FormatDate(self, event_object):
    """Formats the date.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the date field.
    """
    try:
      date_use = timelib.Timestamp.CopyToDatetime(
          event_object.timestamp, self._output_mediator.timezone,
          raise_error=True)
    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, 'store_number', u''),
              getattr(event_object, 'store_index', u'')))
      return u'0000-00-00'
    return u'{0:04d}-{1:02d}-{2:02d}'.format(
        date_use.year, date_use.month, date_use.day)

  def _FormatDateTime(self, event_object):
    """Formats the date and time in ISO 8601 format.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the date field.
    """
    try:
      return timelib.Timestamp.CopyToIsoFormat(
          event_object.timestamp, timezone=self._output_mediator.timezone,
          raise_error=True)

    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, 'store_number', u''),
              getattr(event_object, 'store_index', u'')))

      return u'0000-00-00T00:00:00'

  def _FormatHostname(self, event_object):
    """Formats the hostname.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the hostname field.
    """
    hostname = self._output_mediator.GetHostname(event_object)
    return self._SanitizeField(hostname)

  def _FormatMessage(self, event_object):
    """Formats the message.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the message field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    return self._SanitizeField(message)

  def _FormatMessageShort(self, event_object):
    """Formats the short message.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the short message field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    _, message_short = self._output_mediator.GetFormattedMessages(event_object)
    if message_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    return self._SanitizeField(message_short)

  def _FormatSource(self, event_object):
    """Formats the source.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the source field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    _, source = self._output_mediator.GetFormattedSources(event_object)
    if source is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    return self._SanitizeField(source)

  def _FormatSourceShort(self, event_object):
    """Formats the short source.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the short source field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    source_short, _ = self._output_mediator.GetFormattedSources(event_object)
    if source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    return self._SanitizeField(source_short)

  def _FormatInode(self, event_object):
    """Formats the inode.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the inode field.
    """
    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if hasattr(event_object, 'pathspec') and hasattr(
          event_object.pathspec, 'image_inode'):
        inode = event_object.pathspec.image_inode

    return inode

  def _FormatMACB(self, event_object):
    """Formats the legacy MACB representation.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the MACB field.
    """
    return self._output_mediator.GetMACBRepresentation(event_object)

  def _FormatTag(self, event_object):
    """Formats the event tag.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the event tag field.
    """
    tag = getattr(event_object, 'tag', None)

    if not tag:
      return u'-'

    return u' '.join(tag.tags)

  def _FormatTime(self, event_object):
    """Formats the timestamp.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the timestamp field.
    """
    try:
      date_use = timelib.Timestamp.CopyToDatetime(
          event_object.timestamp, self._output_mediator.timezone,
          raise_error=True)
    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, 'store_number', u''),
              getattr(event_object, 'store_index', u'')))
      return u'00:00:00'
    return u'{0:02d}:{1:02d}:{2:02d}'.format(
        date_use.hour, date_use.minute, date_use.second)

  def _FormatTimestampDescription(self, event_object):
    """Formats the timestamp description.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the timestamp description field.
    """
    return getattr(event_object, 'timestamp_desc', '-')

  def _FormatUsername(self, event_object):
    """Formats the username.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the username field.
    """
    username = self._output_mediator.GetUsername(event_object)
    return self._SanitizeField(username)

  def _FormatZone(self, unused_event_object):
    """Formats the timezone.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the timezone field.
    """
    return self._output_mediator.timezone

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method removes the field delimiter from the field string.

    Args:
      field: the string that makes up the field.

     Returns:
       A string containing the value for the field.
    """
    if self._field_delimiter:
      return field.replace(self._field_delimiter, u' ')
    return field

  def SetFieldsFilter(self, fields_filter):
    """Set the fields filter.

    Args:
      fields_filter: filter object (instance of FilterObject) to
                     indicate which fields should be outputed.
    """
    if not fields_filter:
      return

    if fields_filter.fields:
      self._fields = fields_filter.fields
    if fields_filter.separator:
      self._field_delimiter = fields_filter.separator

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    row = []
    for field in self._fields:
      callback_name = self._FIELD_FORMAT_CALLBACKS.get(field, None)
      callback_function = None
      if callback_name:
        callback_function = getattr(self, callback_name, None)

      if callback_function:
        row.append(callback_function(event_object))
      else:
        row.append(getattr(event_object, field, u'-'))

    out_write = u'{0:s}\n'.format(
        self._field_delimiter.join(unicode(x).replace(
            self._field_delimiter, u' ') for x in row))
    self._WriteLine(out_write)

  def WriteHeader(self):
    """Writes the header to the output."""
    # Start by finding out which fields are to be used.
    self._WriteLine(u'{0:s}\n'.format(self._field_delimiter.join(self._fields)))


manager.OutputManager.RegisterOutput(DynamicOutputModule)
