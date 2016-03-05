# -*- coding: utf-8 -*-
"""Output module for the log2timeline (L2T) CSV format.

For documentation on the L2T CSV format see:
http://forensicswiki.org/wiki/L2T_CSV
"""

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class L2TCSVOutputModule(interface.LinearOutputModule):
  """CSV format used by log2timeline, with 17 fixed fields."""

  NAME = u'l2tcsv'
  DESCRIPTION = u'CSV format used by legacy log2timeline, with 17 fixed fields.'

  _FIELD_DELIMITER = u','
  _HEADER = (
      u'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
      u'version,filename,inode,notes,format,extra\n')

  def _FormatField(self, field):
    """Formats a field.

    Args:
      field: the string that makes up the field.

     Returns:
       A string containing the value for the field.
    """
    if self._FIELD_DELIMITER:
      return field.replace(self._FIELD_DELIMITER, u' ')
    return field

  def _FormatHostname(self, event_object):
    """Formats the hostname.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the hostname field.
    """
    hostname = self._output_mediator.GetHostname(event_object)
    return self._FormatField(hostname)

  def _FormatUsername(self, event_object):
    """Formats the username.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the username field.
    """
    username = self._output_mediator.GetUsername(event_object)
    return self._FormatField(username)

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    if not hasattr(event_object, u'timestamp'):
      return

    message, message_short = self._output_mediator.GetFormattedMessages(
        event_object)
    if message is None or message_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)

    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event_object)
    if format_variables is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    extra_attributes = []
    for attribute_name, attribute_value in sorted(event_object.GetAttributes()):
      if (attribute_name in definitions.RESERVED_VARIABLE_NAMES or
          attribute_name in format_variables):
        continue

      # With ! in {1!s} we force a string conversion since some of
      # the extra attributes values can be integer, float point or
      # boolean values.
      extra_attributes.append(
          u'{0:s}: {1!s} '.format(attribute_name, attribute_value))

    extra_attributes = u' '.join(extra_attributes)
    extra_attributes = extra_attributes.replace(u'\n', u'-').replace(u'\r', u'')

    inode = getattr(event_object, u'inode', u'-')
    if inode == u'-':
      if hasattr(event_object, u'pathspec') and hasattr(
          event_object.pathspec, u'image_inode'):
        inode = event_object.pathspec.image_inode

    hostname = self._FormatHostname(event_object)
    username = self._FormatUsername(event_object)

    notes = []
    note_string = getattr(event_object, u'notes', None)
    if note_string:
      notes.append(note_string)

    tag = getattr(event_object, u'tag', None)
    if tag:
      notes.extend(tag.labels)

    if not notes:
      notes.append(u'-')

    date_string = u'{0:02d}/{1:02d}/{2:04d}'.format(
        date_use.month, date_use.day, date_use.year)
    time_string = u'{0:02d}:{1:02d}:{2:02d}'.format(
        date_use.hour, date_use.minute, date_use.second)

    output_values = (
        date_string,
        time_string,
        u'{0!s}'.format(self._output_mediator.timezone),
        self._output_mediator.GetMACBRepresentation(event_object),
        source_short,
        source,
        getattr(event_object, u'timestamp_desc', u'-'),
        username,
        hostname,
        message_short,
        message,
        u'2',
        getattr(event_object, u'display_name', u'-'),
        u'{0!s}'.format(inode),
        u' '.join(notes),
        getattr(event_object, u'parser', u'-'),
        extra_attributes)

    output_line = u'{0:s}\n'.format(
        u','.join(value.replace(u',', u' ') for value in output_values))
    self._WriteLine(output_line)

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


manager.OutputManager.RegisterOutput(L2TCSVOutputModule)
