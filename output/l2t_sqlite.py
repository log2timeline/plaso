#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright David Nides (davnads.blogspot.com). All Rights Reserved.
# Thank you Eric Wong for assistance.
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

import datetime
import pytz
import re
import sys
import sqlite3

from plaso.proto import plaso_storage_pb2
from plaso.lib import output


class L2R(output.LogOutputFormatter):
  """Contains functions for outputing as l2t_R sqlite database."""

  SKIP = frozenset(['username', 'inode', 'hostname', 'body', 'parser'])

  # Few regular expressions.
  MODIFIED_RE = re.compile(r'modif', re.I)
  ACCESS_RE = re.compile(r'visit', re.I)
  CREATE_RE = re.compile(r'(create|written)', re.I)

  def __init__(self, filehandle=sys.stdout, zone=pytz.utc,
               fields=['host','user','source','sourcetype',
                       'type','datetime','key','color'],
               append=False):
    """Constructor for the output module.

    Args:
      filehandle: A file-like object that can be written to.
      zone: The output time zone (a pytz object).
      fields: The fields to create index for.
      append: Whether to create a new db or appending to an existing one.
    """
    output.LogOutputFormatter.__init__(self, filehandle, zone)
    self.fields = fields
    self.dbname = filehandle.name
    self.append = append

  def Usage(self):
    """Return a quick help message that describes the output provided."""
    return ('l2t_R sqlite database format. database with one table, which'
            'has 17 fields e.g. user, host, date, etc.')

  # Override LogOutputFormatter methods so it won't write to the file
  # handle any more.
  def Start(self):
    """Connect to the database and create the table before inserting."""
    if self.filehandle == sys.stdout:
      raise IOError('Can\'t connect to stdout as database, '
                    'please specify a file.')
    self.filehandle.close()

    self.conn = sqlite3.connect(self.dbname)
    self.conn.text_factory = str
    self.curs = self.conn.cursor()

    # Create table in database.
    if not self.append:
      self.curs.execute(
          ('CREATE TABLE log2timeline (date date, time time, timezone TEXT, '
           'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, user TEXT, '
           'host TEXT, short TEXT, desc TEXT, version TEXT, filename '
           'TEXT, inode TEXT, notes TEXT, format TEXT, extra TEXT, datetime '
           'datetime, reportnotes TEXT, inreport TEXT, key rowid, tag TEXT,'
           'color TEXT, store_number INT, store_index INT)'))

    self.count = 0

  def End(self):
    """Create indices and commit the transaction."""
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for fn in self.fields:
        ciSQL = 'CREATE INDEX %s_idx ON log2timeline (%s)' % (fn, fn)
        self.curs.execute(ciSQL)
    self.conn.commit()
    self.curs.close()
    self.conn.close()

  def StartEvent(self):
    """Do nothing, just override the parent's StartEvent method."""
    pass

  def EndEvent(self):
    """Do nothing, just override the parent's EndEvent method"""
    pass

  def EventBody(self, proto_read):
    """Formats data as l2t_R database table format and writes to the db.

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

    inode = attributes.get('inode', '')
    if not inode:
      if proto_read.pathspec.HasField('image_inode'):
        inode = proto_read.pathspec.image_inode
      else:
        inode = '-'

    row = ( date_use.strftime('%Y-%m-%d'),
            date_use.strftime('%H:%M:%S'),
            str(self.zone),
            self.GetLegacy(proto_read),
            proto_read.DESCRIPTOR.enum_types_by_name[
              'SourceShort'].values_by_number[
                proto_read.source_short].name,
            proto_read.source_long,
            proto_read.timestamp_desc,
            attributes.get('username', '-'),
            attributes.get('hostname', '-'),
            proto_read.description_short.replace('\r', '').replace('\n', ''),
            proto_read.description_long.replace('\r', '').replace('\n', ''),
            '2',
            proto_read.filename,
            inode,
            attributes.get('notes', '-'),  # Notes field placeholder.
            attributes.get('parser', '-'),
            extra,
            date_use.strftime('%Y-%m-%d %H:%M:%S'),
            '',
            '',
            self.count,
            '',
            '',
            proto_read.store_number,
            proto_read.store_index)
    self.curs.execute(
        ('INSERT INTO log2timeline(date, time, timezone, MACB, source, '
         'sourcetype, type, user, host, short, desc, version, filename, '
         'inode, notes, format, extra, datetime, reportnotes, inreport,'
         'key, tag, color, store_number, store_index) VALUES (?, ?, ?, ?'
         ', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,'
         '?, ?, ?, ?, ?, ?, ?, ?)'), row)

    self.count += 1

    # Commit the current transaction every 10000 inserts.
    if self.count % 10000 == 0:
      self.conn.commit()

  def GetLegacy(self, event_proto):
    """Return a legacy MACB representation of the event."""
    # TODO: Fix this function when the MFT parser has been implemented.
    # The filestat parser is somewhat limited.
    # Also fix this when duplicate entries have been implemented so that
    # the function actually returns more than a single entry (as in combined).
    if event_proto.source_short == plaso_storage_pb2.EventObject.FILE:
      letter = event_proto.timestamp_desc[0]

      if letter == 'm':
        return 'M...'
      elif letter == 'a':
        return '.A..'
      elif letter == 'c':
        return '..C.'
      else:
        return '....'

    letters = []
    m = self.MODIFIED_RE.search(event_proto.timestamp_desc)
    if m:
      letters.append('M')
    else:
      letters.append('.')

    m = self.ACCESS_RE.search(event_proto.timestamp_desc)

    if m:
      letters.append('A')
    else:
      letters.append('.')

    m = self.CREATE_RE.search(event_proto.timestamp_desc)

    if m:
      letters.append('C')
    else:
      letters.append('.')

    letters.append('.')

    return ''.join(letters)
