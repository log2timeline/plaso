# -*- coding: utf-8 -*-
"""Contains a class for outputting in a TLN format.

Output module based on TLN as described by:
http://windowsir.blogspot.com/2010/02/timeline-analysisdo-we-need-standard.html

Fields:
  Time - 32 bit Unix epoch.
  Source - The plugin that produced the data.
  Host - The source host system.
  User - The user associated with the data.
  Description - Message string describing the data.
"""

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class TlnOutputFormatter(interface.FileLogOutputFormatter):
  """Five field TLN pipe delimited outputter."""

  NAME = u'tln'
  DESCRIPTION = u'Five field TLN pipe delimited output formatter.'

  DELIMITER = u'|'

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
        hostname = self._hostnames.get(event_object.store_number, u'')

      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)
        if check_user != '-':
          username = check_user

    out_write = u'{0!s}|{1:s}|{2:s}|{3:s}|{4!s}\n'.format(
        date_use,
        source_short.replace(self.DELIMITER, u' '),
        hostname.replace(self.DELIMITER, u' '),
        username.replace(self.DELIMITER, u' '),
        msg.replace(self.DELIMITER, u' '))
    self.filehandle.WriteLine(out_write)

  def WriteHeader(self):
    """Writes the header to the output."""
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
    self.filehandle.WriteLine(u'Time|Source|Host|User|Description\n')


manager.OutputManager.RegisterOutput(TlnOutputFormatter)
