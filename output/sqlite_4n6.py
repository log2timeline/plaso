#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
import os
import re
import sys

from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import output
from plaso.lib import timelib
from plaso.lib import utils
from plaso.output import helper
from plaso import formatters
import pytz
import sqlite3

__author__ = 'David Nides (david.nides@gmail.com)'


class Sql4n6(output.LogOutputFormatter):
  """Contains functions for outputing as 4n6time sqlite database."""

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  META_FIELDS = ['sourcetype', 'source', 'user', 'host', 'MACB',
                 'color', 'type']

  def __init__(self, store, filehandle=sys.stdout, zone=pytz.utc,
               fields=None, append=False, set_status=None):
    """Constructor for the output module.

    Args:
      store: The storage object.
      filehandle: A file-like object that can be written to.
      zone: The output time zone (a pytz object).
      fields: The fields to create index for.
      append: Whether to create a new db or appending to an existing one.
      set_status: Sets status dialog in 4n6time.
    """
    # TODO: Add a unit test for this output module.
    super(Sql4n6, self).__init__(store, filehandle, zone)
    self.set_status = set_status
    # TODO: Revisit handeling this outside of plaso.
    self.dbname = filehandle
    self.append = append
    if fields:
      self.fields = fields
    else:
      self.fields = [
          'host', 'user', 'source', 'sourcetype', 'type', 'datetime', 'color']

  def Usage(self):
    """Return a quick help message that describes the output provided."""
    return '4n6time sqlite database format.'

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
      if self.set_status:
        self.set_status('Created table log2timeline.')

      for field in self.META_FIELDS:
        self.curs.execute(
            'CREATE TABLE l2t_{0}s ({0}s TEXT, frequency INT)'.format(field))
      if self.set_status:
        self.set_status('Created table l2t_%s' % field)

      self.curs.execute('CREATE TABLE l2t_tags (tag TEXT)')
      if self.set_status:
        self.set_status('Created table l2t_tags')

      self.curs.execute('CREATE TABLE l2t_saved_query (name TEXT, query TEXT)')
      if self.set_status:
        self.set_status('Created table l2t_saved_query')

      self.curs.execute('CREATE TABLE l2t_disk (disk_type INT, mount_path TEXT,'
                        ' dd_path TEXT, dd_offset TEXT, export_path TEXT)')
      self.curs.execute('INSERT INTO l2t_disk (disk_type, mount_path, dd_path,'
                        'dd_offset, export_path) VALUES (0, "", "", "", "")')
      if self.set_status:
        self.set_status('Created table l2t_disk')

    self.count = 0

  def End(self):
    """Create indices and commit the transaction."""
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for fn in self.fields:
        sql = 'CREATE INDEX {0}_idx ON log2timeline ({0})'.format(fn)
        self.curs.execute(sql)
        if self.set_status:
          self.set_status('Created index for %s' % fn)

    # Get meta info and save into their tables.
    if self.set_status:
      self.set_status('Checking meta data...')

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

    if self.set_status:
      self.set_status('Database created.')

    self.conn.commit()
    self.curs.close()
    self.conn.close()

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types."""
    self.curs.execute(
        u'SELECT {0}, COUNT({0}) FROM log2timeline GROUP BY {0}'.format(
            field_name))
    res = {}
    for row in self.curs.fetchall():
      if row[0]:
        res[row[0]] = int(row[1])
    return res

  def _ListTags(self):
    """Query database for unique tag types."""
    all_tags = []
    self.curs.execute(
        'SELECT DISTINCT tag FROM log2timeline')

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
    """Do nothing, just override the parent's EndEvent method."""
    pass

  def EventBody(self, event_object):
    """Formats data as 4n6time database table format and writes to the db.

    Args:
      event_object: The event object (EventObject).

    Raises:
      raise errors.NoFormatterFound: If no formatter for this event is found.
    """

    if 'timestamp' not in event_object.GetAttributes():
      return

    formatter = eventdata.EventFormatterManager.GetFormatter(event_object)
    if not formatter:
      raise errors.NoFormatterFound(
          'Unable to output event, no formatter found.')

    msg, msg_short = formatter.GetMessages(event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self.zone)
    extra = []
    format_variables = self.FORMAT_ATTRIBUTE_RE.findall(
        formatter.format_string)
    for key in event_object.GetAttributes():
      if key in utils.RESERVED_VARIABLES or key in format_variables:
        continue
      extra.append('%s: %s ' % (key, getattr(event_object, key, None)))
    extra = ' '.join(extra)

    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if (hasattr(event_object, 'pathspec') and
          hasattr(event_object.pathspec, 'image_inode')):
        inode = event_object.pathspec.image_inode

    date_use_string = '%04d-%02d-%02d %02d:%02d:%02d' %(
        date_use.month, date_use.day, date_use.year, date_use.hour,
        date_use.minute, date_use.second)
    row = (str(self.zone),
           helper.GetLegacy(event_object),
           getattr(event_object, 'source_short', 'LOG'),
           event_object.source_long,
           event_object.timestamp_desc,
           getattr(event_object, 'username', '-'),
           getattr(event_object, 'hostname', '-'),
           msg_short,
           msg,
           '2',
           getattr(event_object, 'filename', '-'),
           inode,
           getattr(event_object, 'notes', '-'),
           getattr(event_object, 'parser', '-'),
           extra,
           date_use_string,
           '',
           '',
           '',
           '',
           event_object.offset,
           event_object.store_number,
           event_object.store_index,
           self.GetVSSNumber(event_object))

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
      if self.set_status:
        self.set_status('Inserting event: %s' % self.count)

  def GetVSSNumber(self, event_object):
    """Return the vss_store_number of the event."""
    if not hasattr(event_object, 'pathspec'):
      return -1

    return getattr(event_object.pathspec, 'vss_store_number', -1)
