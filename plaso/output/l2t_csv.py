# -*- coding: utf-8 -*-
"""Contains functions for outputting as l2t_csv.

Author description at: http://code.google.com/p/log2timeline/wiki/l2t_csv
"""

from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class L2tCsvOutputFormatter(interface.FileLogOutputFormatter):
  """CSV format used by log2timeline, with 17 fixed fields."""

  NAME = u'l2tcsv'
  DESCRIPTION = u'CSV format used by legacy log2timeline, with 17 fixed fields.'

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
    if not hasattr(event_object, u'timestamp'):
      return

    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.data_type))

    msg, msg_short = event_formatter.GetMessages(
        self._formatter_mediator, event_object)
    source_short, source_long = event_formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self.zone)
    extras = []

    format_variables = event_formatter.GetFormatStringAttributeNames()
    for key in event_object.GetAttributes():
      if (key in definitions.RESERVED_VARIABLE_NAMES or
          key in format_variables):
        continue
      value = getattr(event_object, key)

      # With ! in {1!s} we force a string conversion since some of
      # the extra attributes values can be integer, float point or
      # boolean values.
      extras.append(u'{0:s}: {1!s} '.format(key, value))
    extra = u' '.join(extras)

    inode = getattr(event_object, u'inode', u'-')
    if inode == u'-':
      if hasattr(event_object, u'pathspec') and hasattr(
          event_object.pathspec, u'image_inode'):
        inode = event_object.pathspec.image_inode

    hostname = getattr(event_object, u'hostname', u'')

    # TODO: move this into a base output class.
    username = getattr(event_object, u'username', u'-')
    if self.store:
      if not hostname:
        hostname = self._hostnames.get(event_object.store_number, u'-')

      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)
        if check_user != u'-':
          username = check_user

    notes = []
    note_string = getattr(event_object, u'notes', None)
    if note_string:
      notes.append(note_string)

    tag = getattr(event_object, u'tag', None)
    if tag:
      notes.extend(tag.tags)

    if not notes:
      notes.append(u'-')

    row = (
        u'{0:02d}/{1:02d}/{2:04d}'.format(
            date_use.month, date_use.day, date_use.year),
        u'{0:02d}:{1:02d}:{2:02d}'.format(
            date_use.hour, date_use.minute, date_use.second),
        self.zone,
        helper.GetLegacy(event_object),
        source_short,
        source_long,
        getattr(event_object, u'timestamp_desc', u'-'),
        username,
        hostname,
        msg_short,
        msg,
        u'2',
        getattr(event_object, u'display_name', u'-'),
        inode,
        u' '.join(notes),
        getattr(event_object, u'parser', u'-'),
        extra.replace(u'\n', u'-').replace(u'\r', u''))

    out_write = u'{0:s}\n'.format(
        u','.join(unicode(x).replace(u',', u' ') for x in row))
    self.filehandle.WriteLine(out_write)

  def WriteHeader(self):
    """Writes the header to the output."""
    # Build a hostname and username dict objects.
    self._hostnames = {}
    if self.store:
      self._hostnames = helper.BuildHostDict(self.store)
      self._preprocesses = {}
      for info in self.store.GetStorageInformation():
        if hasattr(info, u'store_range'):
          for store_number in range(
              info.store_range[0], info.store_range[1] + 1):
            self._preprocesses[store_number] = info

    self.filehandle.WriteLine(
        u'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        u'version,filename,inode,notes,format,extra\n')


manager.OutputManager.RegisterOutput(L2tCsvOutputFormatter)
