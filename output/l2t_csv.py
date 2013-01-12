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
import datetime
import logging
import pytz
import re

from plaso.output import helper
from plaso.proto import plaso_storage_pb2
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import output


class L2tCsv(output.LogOutputFormatter):
  """Contains functions for outputting as l2t_csv."""

  MICROSEC = int(1e6)  # 1,000,000

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  def Usage(self):
    """Returns a short descrition of what this formatter outputs."""
    return 'l2t_csv format. CSV with 17 fields e.g. user, host, date, etc.'

  def Start(self):
    """Returns a header for the output."""
    self.filehandle.write(('date,time,timezone,MACB,source,sourcetype,type,use'
                           'r,host,short,desc,version,filename,inode,notes,for'
                           'mat,extra\n'))

  def WriteEvent(self, proto):
    """Write a single event."""
    try:
      self.EventBody(proto)
    except errors.NoFormatterFound:
      logging.error('Unable to output line, no formatter found.')
      logging.error(proto)

  def EventBody(self, proto_read):
    """Formats data as l2t_csv and writes to the filehandle from OutputFormater.

    Args:
      proto_read: Protobuf to format.
    """
    formatter = eventdata.GetFormatter(proto_read)
    if not formatter:
      raise errors.NoFormatterFound(
          'Unable to output event, no formatter found.')

    msg, msg_short = formatter.GetMessages()

    try:
      mydate = datetime.datetime.utcfromtimestamp(
          proto_read.timestamp / self.MICROSEC)
    except ValueError as e:
       logging.error(
           u'Unable to print: %s - %d: %s', msg_short,
           proto_read.timestamp, e)
       return
    date_use = mydate.replace(tzinfo=pytz.utc).astimezone(self.zone)

    attributes = formatter.base_attributes
    extra = []
    format_variables = self.FORMAT_ATTRIBUTE_RE.findall(
        formatter.FORMAT_STRING)
    for key, value in attributes.iteritems():
      if key in helper.RESERVED_VARIABLES or key in format_variables:
        continue
      extra.append('%s: %s ' % (key, value))
    extra = ' '.join(extra)

    inode = attributes.get('inode', '')
    if not inode:
      if proto_read.pathspec.HasField('image_inode'):
        inode = proto_read.pathspec.image_inode
      else:
        inode = '-'

    row = (date_use.strftime('%m/%d/%Y'),
           date_use.strftime('%H:%M:%S'),
           self.zone,
           helper.GetLegacy(proto_read),
           proto_read.DESCRIPTOR.enum_types_by_name[
             'SourceShort'].values_by_number[proto_read.source_short].name,
           proto_read.source_long,
           proto_read.timestamp_desc,
           attributes.get('username', '-'),
           attributes.get('hostname', '-'),
           msg_short,
           msg,
           '2',
           proto_read.filename,
           inode,
           attributes.get('notes', '-'),  # Notes field placeholder.
           attributes.get('parser', '-'),
           extra)

    out_write = u'{0}\n'.format(
        u','.join(unicode(x).replace(',', ' ') for x in row))
    self.filehandle.write(out_write.encode('utf-8'))

