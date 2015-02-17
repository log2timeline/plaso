# -*- coding: utf-8 -*-
"""Contains functions for outputting as l2t_csv.

Author description at: http://code.google.com/p/log2timeline/wiki/l2t_csv
"""

import logging

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.lib import utils
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class L2tCsvOutputFormatter(interface.FileLogOutputFormatter):
  """CSV format used by log2timeline, with 17 fixed fields."""

  NAME = u'l2tcsv'
  DESCRIPTION = u'CSV format used by legacy log2timeline, with 17 fixed fields.'

  def Start(self):
    """Returns a header for the output."""
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

  def WriteEvent(self, event_object):
    """Write a single event."""
    try:
      self.EventBody(event_object)
    except errors.NoFormatterFound:
      logging.error(u'Unable to output line, no formatter found.')
      logging.error(event_object)

  def EventBody(self, event_object):
    """Formats data as l2t_csv and writes to the filehandle from OutputFormater.

    Args:
      event_object: The event object (instance of EventObject).

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

    msg, msg_short = event_formatter.GetMessages(event_object)
    source_short, source_long = event_formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self.zone)
    extras = []

    format_variables = event_formatter.GetFormatStringAttributeNames()
    for key in event_object.GetAttributes():
      if key in utils.RESERVED_VARIABLES or key in format_variables:
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
        getattr(event_object, u'notes', u'-'),  # Notes field placeholder.
        getattr(event_object, u'parser', u'-'),
        extra.replace(u'\n', u'-').replace(u'\r', u''))

    out_write = u'{0:s}\n'.format(
        u','.join(unicode(x).replace(u',', u' ') for x in row))
    self.filehandle.WriteLine(out_write)


manager.OutputManager.RegisterOutput(L2tCsvOutputFormatter)
