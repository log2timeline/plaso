# -*- coding: utf-8 -*-
"""Output module for the log2timeline (L2T) CSV format.

For documentation on the L2T CSV format see:
http://forensicswiki.org/wiki/L2T_CSV
"""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.output import interface
from plaso.output import logger
from plaso.output import manager


class L2TCSVOutputModule(interface.LinearOutputModule):
  """CSV format used by log2timeline, with 17 fixed fields."""

  NAME = 'l2tcsv'
  DESCRIPTION = 'CSV format used by legacy log2timeline, with 17 fixed fields.'

  _FIELD_DELIMITER = ','
  _HEADER = (
      'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
      'version,filename,inode,notes,format,extra\n')

  def _FormatField(self, field):
    """Formats a field.

    Args:
      field (str): field value.

     Returns:
       str: formatted field value.
    """
    if self._FIELD_DELIMITER and isinstance(field, py2to3.STRING_TYPES):
      return field.replace(self._FIELD_DELIMITER, ' ')
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

  def _GetOutputValues(self, event):
    """Retrieves output values.

    Args:
      event (EventObject): event.

    Returns:
      list[str]: output values or None if no timestamp was present in the event.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event.
    """
    if not hasattr(event, 'timestamp'):
      logger.error('Unable to output event without timestamp.')
      return None

    # TODO: add function to pass event_values to GetFormattedMessages.
    message, message_short = self._output_mediator.GetFormattedMessages(event)
    if message is None or message_short is None:
      data_type = getattr(event, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    # TODO: add function to pass event_values to GetFormattedSources.
    source_short, source = self._output_mediator.GetFormattedSources(event)
    if source is None or source_short is None:
      data_type = getattr(event, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    # TODO: preserve dfdatetime as an object.
    # TODO: add support for self._output_mediator.timezone
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)

    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event)
    if format_variables is None:
      data_type = getattr(event, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    extra_attributes = []
    for attribute_name, attribute_value in sorted(event.GetAttributes()):
      if (attribute_name in definitions.RESERVED_VARIABLE_NAMES or
          attribute_name in format_variables):
        continue

      # With ! in {1!s} we force a string conversion since some of
      # the extra attributes values can be integer, float point or
      # boolean values.
      extra_attributes.append(
          '{0:s}: {1!s}'.format(attribute_name, attribute_value))

    extra_attributes = '; '.join(extra_attributes)
    extra_attributes = extra_attributes.replace('\n', '-').replace('\r', '')

    inode = getattr(event, 'inode', None)
    if inode is None:
      if hasattr(event, 'pathspec') and hasattr(
          event.pathspec, 'image_inode'):
        inode = event.pathspec.image_inode
    if inode is None:
      inode = '-'

    hostname = self._FormatHostname(event)
    username = self._FormatUsername(event)

    notes = []
    note_string = getattr(event, 'notes', None)
    if note_string:
      notes.append(note_string)

    tag = getattr(event, 'tag', None)
    if tag:
      notes.extend(tag.labels)

    if not notes:
      notes.append('-')

    year, month, day_of_month = date_time.GetDate()
    hours, minutes, seconds = date_time.GetTimeOfDay()
    try:
      date_string = '{0:02d}/{1:02d}/{2:04d}'.format(month, day_of_month, year)
      time_string = '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)
    except (TypeError, ValueError):
      self._ReportEventError(event, (
          'unable to copy timestamp: {0!s} to a human readable date and time. '
          'Defaulting to: "00/00/0000" "--:--:--"').format(event.timestamp))

      date_string = '00/00/0000'
      time_string = '--:--:--'

    output_values = [
        date_string,
        time_string,
        '{0!s}'.format(self._output_mediator.timezone),
        '....',
        source_short,
        source,
        '-',
        username,
        hostname,
        message_short,
        message,
        '2',
        getattr(event, 'display_name', '-'),
        '{0!s}'.format(inode),
        ' '.join(notes),
        getattr(event, 'parser', '-'),
        extra_attributes]

    return output_values

  def _WriteOutputValues(self, output_values):
    """Writes values to the output.

    Args:
      output_values (list[str]): output values.
    """
    for index, value in enumerate(output_values):
      if not isinstance(value, py2to3.STRING_TYPES):
        value = ''
      output_values[index] = value.replace(',', ' ')

    output_line = ','.join(output_values)
    output_line = '{0:s}\n'.format(output_line)
    self._output_writer.Write(output_line)

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
    output_values[6] = event.timestamp_desc or '-'

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
    output_values[6] = '; '.join(timestamp_descriptions)

    self._WriteOutputValues(output_values)

  def WriteHeader(self):
    """Writes the header to the output."""
    self._output_writer.Write(self._HEADER)


manager.OutputManager.RegisterOutput(L2TCSVOutputModule)
