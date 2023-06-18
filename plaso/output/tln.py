# -*- coding: utf-8 -*-
"""Output module for the TLN format.

For documentation on the TLN format see:
  https://forensics.wiki/tln
"""

from plaso.output import formatting_helper
from plaso.output import manager
from plaso.output import shared_dsv


class TLNFieldFormattingHelper(formatting_helper.FieldFormattingHelper):
  """TLN output module field formatting helper."""

  _DESCRIPTION_FIELD_DELIMITER = ';'

  _FIELD_FORMAT_CALLBACKS = {
      'description': '_FormatDescription',
      'host': '_FormatHostname',
      'inode': '_FormatInode',
      'notes': '_FormatNotes',
      'source': '_FormatSourceShort',
      'time': '_FormatTimestamp',
      'tz': '_FormatTimeZone',
      'user': '_FormatUsername',
      'values': '_FormatValues'}

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

  def _FormatDescription(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a description field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: description field.
    """
    date_time_string = self._FormatDateTime(
        output_mediator, event, event_data, event_data_stream)
    timestamp_description = event.timestamp_desc or 'UNKNOWN'

    message = self._FormatMessage(
        output_mediator, event, event_data, event_data_stream)
    message = message.replace(self._DESCRIPTION_FIELD_DELIMITER, ' ')

    return '{0:s}; {1:s}; {2:s}'.format(
        date_time_string, timestamp_description, message)

  def _FormatNotes(self, output_mediator, event, event_data, event_data_stream):
    """Formats a notes field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

     Returns:
       str: formatted notes field.
    """
    inode = self._FormatInode(
        output_mediator, event, event_data, event_data_stream)

    notes = getattr(event_data, 'notes', '')
    if not notes:
      display_name = self._FormatDisplayName(
          output_mediator, event, event_data, event_data_stream)
      notes = 'File: {0:s}'.format(display_name)

      if inode != '-':
        notes = '{0:s} inode: {1:s}'.format(notes, inode)

    return notes

  def _FormatTimestamp(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a timestamp.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: POSIX timestamp in seconds or 0 on error.
    """
    if event.date_time:
      posix_timestamp = event.date_time.CopyToPosixTimestamp()
    else:
      posix_timestamp, _ = divmod(event.timestamp, 1000000)

    return '{0:d}'.format(posix_timestamp or 0)

  # pylint: enable=unused-argument


class TLNOutputModule(shared_dsv.DSVOutputModule):
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

  _FIELD_NAMES = ['time', 'source', 'host', 'user', 'description']

  _HEADER = 'Time|Source|Host|User|Description'

  def __init__(self):
    """Initializes an output module."""
    field_formatting_helper = TLNFieldFormattingHelper()
    super(TLNOutputModule, self).__init__(
        field_formatting_helper, self._FIELD_NAMES, delimiter='|',
        header=self._HEADER)


class L2TTLNOutputModule(shared_dsv.DSVOutputModule):
  """Output module for the log2timeline extended variant of the TLN format.

  l2tTLN is an extended variant of TLN introduced log2timeline.pl 0.65.

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

  _FIELD_NAMES = [
      'time', 'source', 'host', 'user', 'description', 'tz', 'notes']

  _HEADER = 'Time|Source|Host|User|Description|TZ|Notes'

  def __init__(self):
    """Initializes an output module."""
    field_formatting_helper = TLNFieldFormattingHelper()
    super(L2TTLNOutputModule, self).__init__(
        field_formatting_helper, self._FIELD_NAMES, delimiter='|',
        header=self._HEADER)


manager.OutputManager.RegisterOutputs([L2TTLNOutputModule, TLNOutputModule])
