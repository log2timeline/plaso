# -*- coding: utf-8 -*-
"""Output module for the TLN format.

For documentation on the TLN format see: http://forensicswiki.org/wiki/TLN
"""

import sys

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class TLNBaseOutputFormatter(interface.FileOutputModule):
  """Base class for a TLN output module."""
  # Stop pylint from complaining about missing WriteEventBody.
  # pylint: disable=abstract-method

  _FIELD_DELIMITER = u'|'
  _DESCRIPTION_FIELD_DELIMITER = u';'

  _HEADER = u''

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes output module object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: The formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.

    Raises:
      ValueError: if the filehandle value is not supported.
    """
    super(TLNBaseOutputFormatter, self).__init__(
        store, formatter_mediator, filehandle=filehandle, config=config,
        filter_use=filter_use)
    self._hostnames = {}
    self._preprocesses = {}

  def _FormatDescription(self, event_object, event_formatter):
    """Formats the description.

    Args:
      event_object: the event object (instance of EventObject).
      event_formatter: the event formatter (instance of EventFormatter).

     Returns:
       A string containing the value for the description field.
    """
    date_time_string = timelib.Timestamp.CopyToIsoFormat(
        event_object.timestamp, timezone=self._timezone)
    timestamp_description = getattr(event_object, u'timestamp_desc', u'UNKNOWN')
    message, _ = event_formatter.GetMessages(
        self._formatter_mediator, event_object)

    description = u'{0:s}; {1:s}; {2:s}'.format(
        date_time_string, timestamp_description,
        message.replace(self._DESCRIPTION_FIELD_DELIMITER, u' '))
    return description.replace(self._FIELD_DELIMITER, u' ')

  def _FormatHostname(self, event_object):
    """Formats the hostname.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the hostname field.
    """
    hostname = getattr(event_object, u'hostname', u'')
    if not hostname and self.store:
      hostname = self._hostnames.get(event_object.store_number, u'')

    return hostname.replace(self._FIELD_DELIMITER, u' ')

  def _FormatSource(self, event_object, event_formatter):
    """Formats the source.

    Args:
      event_object: the event object (instance of EventObject).
      event_formatter: the event formatter (instance of EventFormatter).

     Returns:
       A string containing the value for the source field.
    """
    source_short, _ = event_formatter.GetSources(event_object)
    return source_short.replace(self._FIELD_DELIMITER, u' ')

  def _FormatUsername(self, event_object):
    """Formats the username.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the username field.
    """
    username = getattr(event_object, u'username', u'')
    if self.store:
      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)
        if check_user != u'-':
          username = check_user

    return username.replace(self._FIELD_DELIMITER, u' ')

  def WriteHeader(self):
    """Writes the header to the output."""
    # Build a hostname and username dict objects.
    if self.store:
      self._hostnames = helper.BuildHostDict(self.store)
      for info in self.store.GetStorageInformation():
        if hasattr(info, u'store_range'):
          for store_number in range(
              info.store_range[0], info.store_range[1] + 1):
            self._preprocesses[store_number] = info

    self._WriteLine(self._HEADER)


class TLNOutputFormatter(TLNBaseOutputFormatter):
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

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    if not hasattr(event_object, u'timestamp'):
      return

    event_formatter = self._GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.data_type))

    posix_timestamp = timelib.Timestamp.CopyToPosix(event_object.timestamp)
    source = self._FormatSource(event_object, event_formatter)
    hostname = self._FormatHostname(event_object)
    username = self._FormatUsername(event_object)
    description = self._FormatDescription(event_object, event_formatter)

    out_write = u'{0:d}|{1:s}|{2:s}|{3:s}|{4!s}\n'.format(
        posix_timestamp, source, hostname, username, description)
    self._WriteLine(out_write)


class L2TTLNOutputFormatter(TLNBaseOutputFormatter):
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

  def _FormatNotes(self, event_object):
    """Formats the notes.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A string containing the value for the notes field.
    """
    notes = getattr(event_object, u'notes', u'')
    if not notes:
      notes = u'File: {0:s} inode: {1!s}'.format(
          getattr(event_object, u'display_name', u''),
          getattr(event_object, u'inode', u''))
    return notes.replace(self._FIELD_DELIMITER, u' ')

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    if not hasattr(event_object, u'timestamp'):
      return

    event_formatter = self._GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.data_type))

    posix_timestamp = timelib.Timestamp.CopyToPosix(event_object.timestamp)
    source = self._FormatSource(event_object, event_formatter)
    hostname = self._FormatHostname(event_object)
    username = self._FormatUsername(event_object)
    description = self._FormatDescription(event_object, event_formatter)
    notes = self._FormatNotes(event_object)

    out_write = u'{0:d}|{1:s}|{2:s}|{3:s}|{4:s}|{5:s}|{6!s}\n'.format(
        posix_timestamp, source, hostname, username, description,
        self._timezone, notes)

    self._WriteLine(out_write)


manager.OutputManager.RegisterOutputs([
    L2TTLNOutputFormatter, TLNOutputFormatter])
