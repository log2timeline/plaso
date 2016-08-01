# -*- coding: utf-8 -*-
"""Output module for the TLN format.

For documentation on the TLN format see: http://forensicswiki.org/wiki/TLN
"""

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class TLNBaseOutputModule(interface.LinearOutputModule):
  """Base class for a TLN output module."""
  # Stop pylint from complaining about missing WriteEventBody.
  # pylint: disable=abstract-method

  _FIELD_DELIMITER = u'|'
  _DESCRIPTION_FIELD_DELIMITER = u';'

  _HEADER = u''

  def _FormatDescription(self, event):
    """Formats the description.

    Args:
      event (EventObject): event.

    Returns:
      str: formatted description field.
    """
    date_time_string = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp, timezone=self._output_mediator.timezone)
    timestamp_description = getattr(event, u'timestamp_desc', u'UNKNOWN')

    message, _ = self._output_mediator.GetFormattedMessages(event)
    if message is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    description = u'{0:s}; {1:s}; {2:s}'.format(
        date_time_string, timestamp_description,
        message.replace(self._DESCRIPTION_FIELD_DELIMITER, u' '))
    return self._SanitizeField(description)

  def _FormatHostname(self, event):
    """Formats the hostname.

    Args:
      event (EventObject): event.

     Returns:
       str: formatted hostname field.
    """
    hostname = self._output_mediator.GetHostname(event)
    return self._SanitizeField(hostname)

  def _FormatSource(self, event):
    """Formats the source.

    Args:
      event (EventObject): event.

     Returns:
       str: formatted source field.
    """
    source_short, _ = self._output_mediator.GetFormattedSources(event)
    if source_short is None:
      data_type = getattr(event, u'data_type', u'UNKNOWN')
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    return self._SanitizeField(source_short)

  def _FormatUsername(self, event):
    """Formats the username.

    Args:
      event (EventObject): event.

     Returns:
       str: formatted username field.
    """
    username = self._output_mediator.GetUsername(event)
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
      return field.replace(self._FIELD_DELIMITER, u' ')
    return field

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


class TLNOutputModule(TLNBaseOutputModule):
  """Output module for the TLN format.

  TLN defines 5 | separated fields, namely:
  * Time - 32-bit POSIX (or Unix) epoch timestamp.
  * Source - The name of the parser or plugin that produced the event.
  * Host - The source host system.
  * User - The user associated with the data.
  * Description - Message string describing the data.
  """
  NAME = u'tln'
  DESCRIPTION = u'TLN 5 field | delimited output.'

  _HEADER = u'Time|Source|Host|User|Description\n'

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    if not hasattr(event, u'timestamp'):
      return

    posix_timestamp = timelib.Timestamp.CopyToPosix(event.timestamp)
    source = self._FormatSource(event)
    hostname = self._FormatHostname(event)
    username = self._FormatUsername(event)
    description = self._FormatDescription(event)

    out_write = u'{0:d}|{1:s}|{2:s}|{3:s}|{4!s}\n'.format(
        posix_timestamp, source, hostname, username, description)
    self._WriteLine(out_write)


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
  NAME = u'l2ttln'
  DESCRIPTION = u'Extended TLN 7 field | delimited output.'

  _HEADER = u'Time|Source|Host|User|Description|TZ|Notes\n'

  def _FormatNotes(self, event):
    """Formats the notes.

    Args:
      event (EventObject): event.

     Returns:
       str: formatted notes field.
    """
    inode = event.inode
    if inode is None:
      inode = u'-'

    notes = getattr(event, u'notes', u'')
    if not notes:
      display_name = getattr(event, u'display_name', u'')
      notes = u'File: {0:s} inode: {1!s}'.format(display_name, inode)
    return self._SanitizeField(notes)

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    if not hasattr(event, u'timestamp'):
      return

    posix_timestamp = timelib.Timestamp.CopyToPosix(event.timestamp)
    source = self._FormatSource(event)
    hostname = self._FormatHostname(event)
    username = self._FormatUsername(event)
    description = self._FormatDescription(event)
    notes = self._FormatNotes(event)

    out_write = u'{0:d}|{1:s}|{2:s}|{3:s}|{4:s}|{5!s}|{6!s}\n'.format(
        posix_timestamp, source, hostname, username, description,
        self._output_mediator.timezone, notes)

    self._WriteLine(out_write)


manager.OutputManager.RegisterOutputs([L2TTLNOutputModule, TLNOutputModule])
