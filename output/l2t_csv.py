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
import pytz

from plaso.lib import output


class L2tCsv(output.LogOutputFormatter):
  """Contains functions for outputting as l2t_csv."""

  SKIP = frozenset(['username', 'inode', 'hostname', 'body'])
  US = int(1e6)  # 1,000,000

  def Usage(self):
    """Returns a short descrition of what this formatter outputs."""
    return 'l2t_csv format. CSV with 17 fields e.g. user, host, date, etc.'

  def Start(self):
    """Returns a header for the output."""
    self.filehandle.write(('date,time,timezone,MACB,source,sourcetype,type,use'
                           'r,host,short,desc,version,filename,inode,notes,for'
                           'mat,extra\n'))

  def EventBody(self, proto_read):
    """Formats data as l2t_csv and writes to the filehandle from OutputFormater.

    Args:
      proto_read: Protobuf to format.
    """

    mydate = datetime.datetime.utcfromtimestamp(proto_read.timestamp / 1e6)
    date_use = mydate.replace(tzinfo=pytz.utc).astimezone(self.zone)

    attributes = {}
    attributes = dict((a.key, a.value) for a in proto_read.attributes)
    extra = []
    for key, value in attributes.iteritems():
      if key in self.SKIP:
        continue
      extra.append('%s: %s ' % (key, value))
    extra = ' '.join(extra)

    row = (date_use.strftime('%m/%d/%Y'),
           date_use.strftime('%H:%M:%S'),
           self.zone,
           # TODO: Implement a MACB function. Hard coding for now.
           '....',
           proto_read.DESCRIPTOR.enum_types_by_name['SourceShort'].values_by_number[
               proto_read.source_short].name,
           proto_read.source_long,
           proto_read.timestamp_desc,
           attributes.get('username', '-'),
           attributes.get('hostname', '-'),
           proto_read.description_short.replace('\r', '').replace('\n', ''),
           proto_read.description_long.replace('\r', '').replace('\n', ''),
           '2',
           proto_read.display_name,
           # TODO: Consider extracting from proto_read.pathspec.image_ino
           attributes.get('inode', '-'),
           attributes.get('notes', '-'),  # Notes field placeholder.
           '-',  # Name of the parser (still missing).
           extra)

    out_write = u'{0}\n'.format(
        u','.join(unicode(x).replace(',', ' ') for x in row))
    self.filehandle.write(out_write.encode('utf-8'))
