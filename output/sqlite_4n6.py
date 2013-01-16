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

import logging
import pytz
import os
import re
import sys
import sqlite3

from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import output
from plaso.lib import timelib
from plaso.output import helper
from plaso.proto import transmission_pb2

__author__ = 'David Nides (david.nides@gmail.com)'


class Sql4n6(output.LogOutputFormatter):
  """Contains functions for outputing as 4n6time sqlite database."""

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  META_FIELDS = ['sourcetype', 'source', 'user', 'host', 'MACB',
                 'color', 'type']

  def __init__(self, filehandle=sys.stdout, zone=pytz.utc,
               fields=['host','user','source','sourcetype',
                       'type','datetime','color'],
               append=False):
    """Constructor for the output module.

    Args:
      filehandle: A file-like object that can be written to.
      zone: The output time zone (a pytz object).
      fields: The fields to create index for.
      append: Whether to create a new db or appending to an existing one.
    """
    super(Sql4n6, self).__init__(filehandle, zone)
    self.fields = fields
    self.dbname = filehandle
    self.append = append

  def Usage(self):
    """Return a quick help message that describes the output provided."""
    return ('4n6time sqlite database format. database with one table, which'
            'has 15 fields e.g. user, host, date, etc.')

  # Override LogOutputFormatter methods so it won't write to the file
  # handle any more.
  def Start(self):
    """Connect to the database and create the table before inserting."""
    if self.filehandle == sys.stdout:
      raise IOError('Can\'t connect to stdout as database, '
                    'please specify a file.')

    if os.path.isfile(self.filehandle):
      raise IOError(
          (u'Unable to use an already existing file for output '
           '[%s]' % self.filehandle))

    self.conn = sqlite3.connect(self.dbname)
    self.conn.text_factory = str
    self.curs = self.conn.cursor()

    # Create table in database.
    if not self.append:
      self.curs.execute(
          ('CREATE TABLE log2timeline (timezone TEXT, '
           'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, user TEXT, '
           'host TEXT, short TEXT, desc TEXT, version TEXT, filename '
           'TEXT, inode TEXT, notes TEXT, format TEXT, extra TEXT, datetime '
           'datetime, reportnotes TEXT, inreport TEXT, tag TEXT,'
           'color TEXT, offset INT, store_number INT, store_index INT,'
           'vss_store_number INT)'))
      for field in self.META_FIELDS:
        self.curs.execute(
            'CREATE TABLE l2t_{0}s ({0}s TEXT, frequency INT)'.format(field))
      self.curs.execute('CREATE TABLE l2t_tags (tag TEXT)')

    self.count = 0

  def End(self):
    """Create indices and commit the transaction."""
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for fn in self.fields:
        ciSQL = 'CREATE INDEX %s_idx ON log2timeline (%s)' % (fn, fn)
        self.curs.execute(ciSQL)

    # Get meta info and save into their tables.
    for field in self.META_FIELDS:
      vals = self._GetDistinctValues(field)
      self.curs.execute('DELETE FROM l2t_%ss' % field)
      for name, freq in vals.items():
        self.curs.execute(
            'INSERT INTO l2t_%ss (%ss, frequency) VALUES("%s", %s) ' % (
                field, field, name, freq))
    self.curs.execute('DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self.curs.execute('INSERT INTO l2t_tags (tag) VALUES (?)', tag)

    self.conn.commit()
    self.curs.close()
    self.conn.close()

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types"""
    self.curs.execute(u'SELECT :field, COUNT(:field) FROM \
                      log2timeline GROUP BY :field', {'field': field_name})
    a = self.curs.fetchall()
    res = {}
    for i in a:
      if i[0] != '':
        res[i[0]] = int(i[1])
    return res

  def _ListTags(self):
    """Query database for unique tag types"""
    all_tags = []
    self.curs.execute('SELECT DISTINCT tag \
                      FROM log2timeline')

    # This cleans up the messy SQL return.
    for tag_row in self.curs.fetchall():
      tag_string = tag_row[0]
      if tag_string:
        tags = tag_string.split(',')
        for tag in tags:
          if tag not in all_tags:
            all_tags.append(tag)
    return all_tags

  def StartEvent(self):
    """Do nothing, just override the parent's StartEvent method."""
    pass

  def EndEvent(self):
    """Do nothing, just override the parent's EndEvent method"""
    pass

  def EventBody(self, evt):
    """Formats data as 4n6time database table format and writes to the db.

    Args:
      evt: An EventObject that contains the event data.
    """

    if 'timestamp' not in evt.GetAttributes():
      return

    formatter = eventdata.EventFormatterManager.GetFormatter(evt)
    if not formatter:
      raise errors.NoFormatterFound(
          'Unable to output event, no formatter found.')

    msg, msg_short = formatter.GetMessages(evt)

    date_use = timelib.DateTimeFromTimestamp(evt.timestamp, self.zone)
    if not date_use:
      logging.error(u'Unable to process date for entry: %s', msg)
      return
    extra = []
    format_variables = self.FORMAT_ATTRIBUTE_RE.findall(
        formatter.format_string)
    for key in evt.GetAttributes():
      if key in helper.RESERVED_VARIABLES or key in format_variables:
        continue
      extra.append('%s: %s ' % (key, getattr(evt, key, None)))
    extra = ' '.join(extra)

    inode = getattr(evt, 'inode', '-')
    if inode == '-':
      if hasattr(evt, 'pathspec'):
        pathspec = transmission_pb2.PathSpec()
        pathspec.ParseFromString(evt.pathspec)
        if pathspec.HasField('image_inode'):
          inode = pathspec.image_inode

    row = (str(self.zone),
           helper.GetLegacy(evt),
           getattr(evt, 'source_short', 'LOG'),
           evt.source_long,
           evt.timestamp_desc,
           getattr(evt, 'username', '-'),
           getattr(evt, 'hostname', '-'),
           msg_short,
           msg,
           '2',
           getattr(evt, 'filename', '-'),
           inode,
           getattr(evt, 'notes', '-'),
           getattr(evt, 'parser', '-'),
           extra,
           date_use.strftime('%Y-%m-%d %H:%M:%S'),
           '',
           '',
           '',
           '',
           evt.offset,
           evt.store_number,
           evt.store_index,
           self.GetVSSNumber(evt))

    self.curs.execute(
        ('INSERT INTO log2timeline(timezone, MACB, source, '
         'sourcetype, type, user, host, short, desc, version, filename, '
         'inode, notes, format, extra, datetime, reportnotes, inreport,'
         'tag, color, offset, store_number, store_index, vss_store_number)'
         ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,'
         '?, ?, ?, ?, ?, ?, ?, ?, ?)'), row)

    self.count += 1

    # Commit the current transaction every 10000 inserts.
    if self.count % 10000 == 0:
      self.conn.commit()

  def GetVSSNumber(self, evt):
    """Return the vss_store_number of the event."""
    if not hasattr(evt, 'pathspec'):
      return -1

    pathspec = transmission_pb2.PathSpec()
    pathspec.ParseFromString(evt.pathspec)
    if pathspec.HasField('vss_store_number'):
      return pathspec.vss_store_number
    else:
      return -1
