#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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

from plaso.output import helper
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import output
from plaso.lib import timelib

from plaso.proto import transmission_pb2


class L2tcsv(output.FileLogOutputFormatter):
  """Contains functions for outputting as l2t_csv."""

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  def Usage(self):
    """Returns a short descrition of what this formatter outputs."""
    return 'l2t_csv format. CSV with 17 fields e.g. user, host, date, etc.'

  def Start(self):
    """Returns a header for the output."""
    self.filehandle.write(
        'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        'version,filename,inode,notes,format,extra\n')

  def WriteEvent(self, event_object):
    """Write a single event."""
    try:
      self.EventBody(event_object)
    except errors.NoFormatterFound:
      logging.error('Unable to output line, no formatter found.')
      logging.error(event_object)

  def EventBody(self, event_object):
    """Formats data as l2t_csv and writes to the filehandle from OutputFormater.

    Args:
      event_object: The event object (EventObject).
    """
    event_formatter = eventdata.EventFormatterManager.GetFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          'Unable to find no event formatter for: %s.' % event_object.DATA_TYPE)

    msg, msg_short = event_formatter.GetMessages(event_object)

    if not hasattr(event_object, 'timestamp'):
      return

    date_use = timelib.DateTimeFromTimestamp(event_object.timestamp, self.zone)
    if not date_use:
      logging.error(u'Unable to process date for entry: %s', msg)
      return

    extra = []
    format_variables = self.FORMAT_ATTRIBUTE_RE.findall(
        event_formatter.format_string)
    for key in event_object.GetAttributes():
      if key in helper.RESERVED_VARIABLES or key in format_variables:
        continue
      extra.append('%s: %s ' % (key, getattr(event_object, key)))
    extra = ' '.join(extra)

    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if hasattr(event_object, 'pathspec'):
        pathspec = transmission_pb2.PathSpec()
        pathspec.ParseFromString(event_object.pathspec)
        if pathspec.HasField('image_inode'):
          inode = pathspec.image_inode

    row = (date_use.strftime('%m/%d/%Y'),
           date_use.strftime('%H:%M:%S'),
           self.zone,
           helper.GetLegacy(event_object),
           event_object.source_short,
           event_object.source_long,
           event_object.timestamp_desc,
           getattr(event_object, 'username', '-'),
           getattr(event_object, 'hostname', '-'),
           msg_short,
           msg,
           '2',
           event_object.filename,
           inode,
           getattr(event_object, 'notes', '-'),  # Notes field placeholder.
           getattr(event_object, 'parser', '-'),
           extra)

    out_write = u'{0}\n'.format(
        u','.join(unicode(x).replace(',', ' ') for x in row))
    self.filehandle.write(out_write.encode('utf-8'))

