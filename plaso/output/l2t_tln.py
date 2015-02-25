# -*- coding: utf-8 -*-
"""Contains a class for outputting in the l2tTLN format.

l2tTLN is TLN as expanded in L2T 0.65 to 7 fields:

https://code.google.com/p/log2timeline/source/browse/lib/Log2t/output/tln.pm

Fields:
  Time - 32 bit Unix epoch.
  Source - The plugin that produced the data.
  Host - The source host system.
  User - The user associated with the data.
  Description - Message string describing the data.
  TZ - L2T 0.65 field. Timezone of the event.
  Notes - L2T 0.65 field. Optional notes field or filename and inode.
"""

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class L2tTlnOutputFormatter(interface.FileLogOutputFormatter):
  """Extended seven field pipe delimited TLN; L2T 0.65 style."""

  NAME = u'l2ttln'
  DESCRIPTION = (
      u'Extended seven field pipe delimited TLN, used in legacy log2timeline.')

  DELIMITER = u'|'

  def Start(self):
    """Returns a header for the output."""
    # Build a hostname and username dict objects.
    self._hostnames = {}
    if self.store:
      self._hostnames = helper.BuildHostDict(self.store)
      self._preprocesses = {}
      for info in self.store.GetStorageInformation():
        if hasattr(info, 'store_range'):
          for store_number in range(
              info.store_range[0], info.store_range[1] + 1):
            self._preprocesses[store_number] = info
    self.filehandle.WriteLine(u'Time|Source|Host|User|Description|TZ|Notes\n')

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Each event object contains both attributes that are considered "reserved"
    and others that aren't. The 'raw' representation of the object makes a
    distinction between these two types as well as extracting the format
    strings from the object.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    if not hasattr(event_object, 'timestamp'):
      return

    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.data_type))

    msg, _ = event_formatter.GetMessages(self._formatter_mediator, event_object)
    source_short, _ = event_formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToPosix(event_object.timestamp)
    hostname = getattr(event_object, 'hostname', u'')
    username = getattr(event_object, 'username', u'')

    if self.store:
      if not hostname:
        hostname = self._hostnames.get(event_object.store_number, '')

      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)
        if check_user != '-':
          username = check_user

    notes = getattr(event_object, 'notes', u'')
    if not notes:
      notes = u'File: {0:s} inode: {1!s}'.format(
          getattr(event_object, 'display_name', u''),
          getattr(event_object, 'inode', u''))

    out_write = u'{0!s}|{1:s}|{2:s}|{3:s}|{4:s}|{5:s}|{6!s}\n'.format(
        date_use,
        source_short.replace(self.DELIMITER, u' '),
        hostname.replace(self.DELIMITER, u' '),
        username.replace(self.DELIMITER, u' '),
        msg.replace(self.DELIMITER, u' '),
        self.zone,
        notes.replace(self.DELIMITER, u' '))

    self.filehandle.WriteLine(out_write)


manager.OutputManager.RegisterOutput(L2tTlnOutputFormatter)
