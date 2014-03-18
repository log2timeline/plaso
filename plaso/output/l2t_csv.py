#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains functions for outputting as l2t_csv.

Author description at: http://code.google.com/p/log2timeline/wiki/l2t_csv
"""
import logging
import re

from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import output
from plaso.lib import timelib
from plaso.lib import utils
from plaso.output import helper


class L2tcsv(output.FileLogOutputFormatter):
  """CSV format used by log2timeline, with 17 fixed fields."""

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

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
      event_object: The event object (EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    if not hasattr(event_object, 'timestamp'):
      return

    event_formatter = eventdata.EventFormatterManager.GetFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.DATA_TYPE))

    msg, msg_short = event_formatter.GetMessages(event_object)
    source_short, source_long = event_formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self.zone)
    extras = []
    format_variables = self.FORMAT_ATTRIBUTE_RE.findall(
        event_formatter.format_string)
    for key in event_object.GetAttributes():
      if key in utils.RESERVED_VARIABLES or key in format_variables:
        continue
      extras.append(u'%s: %s ' % (key, getattr(event_object, key)))
    extra = ' '.join(extras)

    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if hasattr(event_object, 'pathspec') and hasattr(
          event_object.pathspec, 'image_inode'):
        inode = event_object.pathspec.image_inode

    hostname = getattr(event_object, 'hostname', u'')

    # TODO: move this into a base output class.
    username = getattr(event_object, 'username', u'-')
    if self.store:
      if not hostname:
        hostname = self._hostnames.get(event_object.store_number, u'-')

      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)
        if check_user != '-':
          username = check_user

    row = ('%02d/%02d/%04d' %(date_use.month, date_use.day, date_use.year),
           '%02d:%02d:%02d' %(date_use.hour, date_use.minute, date_use.second),
           self.zone,
           helper.GetLegacy(event_object),
           source_short,
           source_long,
           getattr(event_object, 'timestamp_desc', u'-'),
           username,
           hostname,
           msg_short,
           msg,
           '2',
           getattr(event_object, 'display_name', u'-'),
           inode,
           getattr(event_object, 'notes', u'-'),  # Notes field placeholder.
           getattr(event_object, 'parser', u'-'),
           extra.replace('\n', u'-').replace('\r', u''))

    out_write = u'{0}\n'.format(
        u','.join(unicode(x).replace(',', u' ') for x in row))
    self.filehandle.WriteLine(out_write)
