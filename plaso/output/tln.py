# -*- coding: utf-8 -*-
"""Output module for the TLN format.

For documentation on the TLN format see: http://forensicswiki.org/wiki/TLN
"""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class TLNBaseOutputModule(interface.LinearOutputModule):
  """Base class for a TLN output module."""
  # Stop pylint from complaining about missing WriteEventBody.
  # pylint: disable=abstract-method

  _FIELD_DELIMITER = '|'
  _DESCRIPTION_FIELD_DELIMITER = ';'

  _HEADER = ''

  def _FormatDescription(self, event, event_data):
    """Formats the description.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      str: formatted description field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event data.
    """
    date_time_string = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp, timezone=self._output_mediator.timezone)
    timestamp_description = event.timestamp_desc or 'UNKNOWN'

    message, _ = self._output_mediator.GetFormattedMessages(event_data)
    if message is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    description = '{0:s}; {1:s}; {2:s}'.format(
        date_time_string, timestamp_description,
        message.replace(self._DESCRIPTION_FIELD_DELIMITER, ' '))
    return self._SanitizeField(description)

  def _FormatHostname(self, event_data):
    """Formats the hostname.

    Args:
      event_data (EventData): event data.

     Returns:
       str: formatted hostname field.
    """
    hostname = self._output_mediator.GetHostname(event_data)
    return self._SanitizeField(hostname)

  def _FormatSource(self, event, event_data):
    """Formats the source.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

     Returns:
       str: formatted source field.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event data.
    """
    source_short, _ = self._output_mediator.GetFormattedSources(
        event, event_data)
    if source_short is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    return self._SanitizeField(source_short)

  def _FormatUsername(self, event_data):
    """Formats the username.

    Args:
      event_data (EventData): event data.

     Returns:
       str: formatted username field.
    """
    username = self._output_mediator.GetUsername(event_data)
    return self._SanitizeField(username)

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method removes the field delimiter from the field string.

    Args:
      field (str): field value.

     Returns:
       str: formatted field value.
    """
    if self._FIELD_DELIMITER and isinstance(field, py2to3.STRING_TYPES):
      return field.replace(self._FIELD_DELIMITER, ' ')
    return field

  def WriteHeader(self):
    """Writes the header to the output."""
    self._output_writer.Write(self._HEADER)


class TLNOutputModule(TLNBaseOutputModule):
  """Output module for the TLN format.

  TLN defines 5 | separated fields, namely:
  * Time - 32-bit POSIX (or Unix) epoch timestamp.
  * Source - The name of the parser or plugin that produced the event.
  * Host - The source host system.
  * User - The user associated with the data.
  * Description - Message string describing the data.
  """
  NAME = 'tln'
  DESCRIPTION = 'TLN 5 field | delimited output.'

  _HEADER = 'Time|Source|Host|User|Description\n'

  # pylint: disable=unused-argument
  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    if not hasattr(event, 'timestamp'):
      return

    # TODO: preserve dfdatetime as an object.
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)
    posix_timestamp = date_time.CopyToPosixTimestamp()
    if not posix_timestamp:
      posix_timestamp = 0

    source = self._FormatSource(event, event_data)
    hostname = self._FormatHostname(event_data)
    username = self._FormatUsername(event_data)
    description = self._FormatDescription(event, event_data)

    out_write = '{0:d}|{1:s}|{2:s}|{3:s}|{4!s}\n'.format(
        posix_timestamp, source, hostname, username, description)
    self._output_writer.Write(out_write)


class L2TTLNOutputModule(TLNBaseOutputModule):
  """Output module for the log2timeline extended variant of the TLN format.

  l2tTLN is an extended variant of TLN introduced log2timeline 0.65.

  l2tTLN extends basic TLN to 7 | separated fields, namely:
  * Time - 32-bit POSIX (or Unix) epoch timestamp.
  * Source - The name of the parser or plugin that produced the event.
  * Host - The source host system.
  * User - The user associated with the data.
  * Description - Message string describing the data.
  * TZ - L2T 0.65 field. Timezone of the event.
  * Notes - L2T 0.65 field. Optional notes field or filename and inode.
  """
  NAME = 'l2ttln'
  DESCRIPTION = 'Extended TLN 7 field | delimited output.'

  _HEADER = 'Time|Source|Host|User|Description|TZ|Notes\n'

  def _FormatInode(self, event_data):
    """Formats the inode.

    Args:
      event_data (EventData): event data.

    Returns:
      str: inode field.
    """
    inode = getattr(event_data, 'inode', None)
    if inode is None:
      pathspec = getattr(event_data, 'pathspec', None)
      if pathspec and hasattr(pathspec, 'inode'):
        inode = pathspec.inode
    if inode is None:
      inode = '-'

    return inode

  def _FormatNotes(self, event_data):
    """Formats the notes.

    Args:
      event_data (EventData): event data.

     Returns:
       str: formatted notes field.
    """
    inode = self._FormatInode(event_data)

    notes = getattr(event_data, 'notes', '')
    if not notes:
      display_name = getattr(event_data, 'display_name', '')
      notes = 'File: {0:s} inode: {1!s}'.format(display_name, inode)
    return self._SanitizeField(notes)

  # pylint: disable=unused-argument
  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    if not hasattr(event, 'timestamp'):
      return

    # TODO: preserve dfdatetime as an object.
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)
    posix_timestamp = date_time.CopyToPosixTimestamp()
    if not posix_timestamp:
      posix_timestamp = 0

    source = self._FormatSource(event, event_data)
    hostname = self._FormatHostname(event_data)
    username = self._FormatUsername(event_data)
    description = self._FormatDescription(event, event_data)
    notes = self._FormatNotes(event_data)

    out_write = '{0:d}|{1:s}|{2:s}|{3:s}|{4:s}|{5!s}|{6!s}\n'.format(
        posix_timestamp, source, hostname, username, description,
        self._output_mediator.timezone, notes)

    self._output_writer.Write(out_write)


manager.OutputManager.RegisterOutputs([L2TTLNOutputModule, TLNOutputModule])
