# -*- coding: utf-8 -*-
"""Output module for the log2timeline (L2T) CSV format.

For documentation on the L2T CSV format see:
http://forensicswiki.org/wiki/L2T_CSV
"""

import logging

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import py2to3
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
      field (str): field value.

     Returns:
       str: formatted field value.
    """
    if self._FIELD_DELIMITER and isinstance(field, py2to3.STRING_TYPES):
      return field.replace(self._FIELD_DELIMITER, u' ')
    return field

  def _FormatHostname(self, event):
    """Formats the hostname.

    Args:
      event (EventObject): event.

     Returns:
       str: formatted hostname field.
    """
    hostname = self._output_mediator.GetHostname(event)
    return self._FormatField(hostname)

  def _FormatUsername(self, event):
    """Formats the username.

    Args:
      event (EventObject): event.

     Returns:
       str: formatted username field.
    """
    username = self._output_mediator.GetUsername(event)
    return self._FormatField(username)

  def _WriteOutputValues(self, output_values):
    """Writes values to the output.

    Args:
      output_values (list[str]): output values.
    """
    for index, value in enumerate(output_values):
      if not isinstance(value, py2to3.STRING_TYPES):
        value = u''
      output_values[index] = value.replace(u',', u' ')

    output_line = u','.join(output_values)
    output_line = u'{0:s}\n'.format(output_line)
    self._WriteLine(output_line)

  def _GetOutputValues(self, event):
    """Retrieves output values.

    Args:
      event (EventObject): event.

    Returns:
      list[str]: output values.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event.
    """
    if not hasattr(event, u'timestamp'):
      logging.error(u'Unable to output event without timestamp.')
      return

    # TODO: add function to pass event_values to GetFormattedMessages.
    message, message_short = self._output_mediator.GetFormattedMessages(event)
    if message is None or message_short is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    # TODO: add function to pass event_values to GetFormattedSources.
    source_short, source = self._output_mediator.GetFormattedSources(event)
    if source is None or source_short is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    date_use = timelib.Timestamp.CopyToDatetime(
        event.timestamp, self._output_mediator.timezone)

    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event)
    if format_variables is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    extra_attributes = []
    for attribute_name, attribute_value in sorted(event.GetAttributes()):
      if (attribute_name in definitions.RESERVED_VARIABLE_NAMES or
          attribute_name in format_variables):
        continue

      # With ! in {1!s} we force a string conversion since some of
      # the extra attributes values can be integer, float point or
      # boolean values.
      extra_attributes.append(
          u'{0:s}: {1!s}'.format(attribute_name, attribute_value))

    extra_attributes = u'; '.join(extra_attributes)
    extra_attributes = extra_attributes.replace(u'\n', u'-').replace(u'\r', u'')

    inode = getattr(event, u'inode', None)
    if inode is None:
      if hasattr(event, u'pathspec') and hasattr(
          event.pathspec, u'image_inode'):
        inode = event.pathspec.image_inode
    if inode is None:
      inode = u'-'

    hostname = self._FormatHostname(event)
    username = self._FormatUsername(event)

    notes = []
    note_string = getattr(event, u'notes', None)
    if note_string:
      notes.append(note_string)

    tag = getattr(event, u'tag', None)
    if tag:
      notes.extend(tag.labels)

    if not notes:
      notes.append(u'-')

    date_string = u'{0:02d}/{1:02d}/{2:04d}'.format(
        date_use.month, date_use.day, date_use.year)
    time_string = u'{0:02d}:{1:02d}:{2:02d}'.format(
        date_use.hour, date_use.minute, date_use.second)

    output_values = [
        date_string,
        time_string,
        u'{0!s}'.format(self._output_mediator.timezone),
        u'....',
        source_short,
        source,
        u'-',
        username,
        hostname,
        message_short,
        message,
        u'2',
        getattr(event, u'display_name', u'-'),
        u'{0!s}'.format(inode),
        u' '.join(notes),
        getattr(event, u'parser', u'-'),
        extra_attributes]

    return output_values

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event object.
    """
    output_values = self._GetOutputValues(event)

    output_values[3] = self._output_mediator.GetMACBRepresentation(event)
    output_values[6] = getattr(event, u'timestamp_desc', u'-')

    self._WriteOutputValues(output_values)

  def WriteEventMACBGroup(self, event_macb_group):
    """Writes an event MACB group to the output.

    Args:
      event_macb_group (list[EventObject]): event MACB group.
    """
    output_values = self._GetOutputValues(event_macb_group[0])

    timestamp_descriptions = [
        event.timestamp_desc for event in event_macb_group]
    output_values[3] = (
        self._output_mediator.GetMACBRepresentationFromDescriptions(
            timestamp_descriptions))
    # TODO: fix timestamp description in source.
    output_values[6] = u'; '.join(timestamp_descriptions)

    self._WriteOutputValues(output_values)

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


manager.OutputManager.RegisterOutput(L2TCSVOutputModule)
