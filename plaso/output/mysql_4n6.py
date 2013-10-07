#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import logging
import re
import sys

from plaso.output import helper
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import output
from plaso.lib import timelib
from plaso.lib import utils

from plaso import formatters
import MySQLdb


__author__ = 'David Nides (david.nides@gmail.com)'


class Mysql4n6(output.LogOutputFormatter):
  """Contains functions for outputing as 4n6time MySQL database."""

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  META_FIELDS = ['sourcetype', 'source', 'user', 'host', 'MACB',
                 'color', 'type', 'record_number']

  def __init__(self, store, filehandle=sys.stdout, config=None,
               filter_use=None):
    """Constructor for the output module.

    Args:
      store: The storage object.
      filehandle: A file-like object that can be written to.
      config: The configuration object for the module.
      filter_use: The filter object used.
    """
    # TODO: Add a unit test for this output module.
    super(Mysql4n6, self).__init__(store, filehandle, config, filter_use)
    self.set_status = getattr(config, 'set_status', None)

    # TODO: Revisit making compatible with plaso cmdline.
    db_info = getattr(config, 'save_info', None)
    if type(db_info) is dict:
      self.host = db_info.get('db_host', '')
      self.user = db_info.get('db_user', '')
      self.password = db_info.get('db_pass', '')
      self.dbname = db_info.get('db_name', '')

    self.evidence = getattr(config, 'evidence', '-')
    self.append = getattr(config, 'append', False)
    self.fields = getattr(config, 'fields', [
        'host', 'user', 'source', 'sourcetype', 'type', 'datetime', 'color'])

  def Start(self):
    """Connect to the database and create the table before inserting."""
    if self.dbname == '':
      raise IOError('Specify a database name.')
     
    try:
      if self.append:
        self.conn = MySQLdb.connect(self.host, self.user,
                                    self.password, self.dbname)
        self.curs = self.conn.cursor()
      else:
        self.conn = MySQLdb.connect(self.host, self.user, self.password)
        self.curs = self.conn.cursor()
        self.curs.execute('SET GLOBAL innodb_large_prefix=ON')
        self.curs.execute('SET GLOBAL innodb_file_format=barracuda')
        self.curs.execute('SET GLOBAL innodb_file_per_table=ON')
        self.curs.execute('CREATE DATABASE %s' % self.dbname)
        self.curs.execute('USE %s' % self.dbname)
        # Create tables.
        self.curs.execute(
            ('CREATE TABLE log2timeline ('
             'rowid INT NOT NULL AUTO_INCREMENT, timezone VARCHAR(256), '
             'MACB VARCHAR(256), source VARCHAR(256), sourcetype VARCHAR(256), '
             'type VARCHAR(256), user VARCHAR(256), host VARCHAR(256), '
             'description TEXT, filename VARCHAR(256), inode VARCHAR(256), '
             'notes VARCHAR(256), format VARCHAR(256), '
             'extra TEXT, datetime datetime, reportnotes VARCHAR(256), '
             'inreport VARCHAR(256), tag VARCHAR(256), color VARCHAR(256), '
             'offset INT, store_number INT, store_index INT, '
             'vss_store_number INT, URL VARCHAR(256), '
             'record_number VARCHAR(256), event_identifier VARCHAR(256), '
             'event_type VARCHAR(256), source_name VARCHAR(256), '
             'user_sid VARCHAR(256), computer_name VARCHAR(256), '
             'evidence VARCHAR(256), '
            'PRIMARY KEY (rowid)) ENGINE=InnoDB ROW_FORMAT=COMPRESSED'))
        if self.set_status:
          self.set_status('Created table: log2timeline.')

        for field in self.META_FIELDS:
          self.curs.execute(
              'CREATE TABLE l2t_{0}s ({0}s TEXT, frequency INT) '
              'ENGINE=InnoDB ROW_FORMAT=COMPRESSED'.format(field))
        if self.set_status:
          self.set_status('Created table: l2t_%s' % field)

        self.curs.execute('CREATE TABLE l2t_tags (tag TEXT) '
                          'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
        if self.set_status:
          self.set_status('Created table: l2t_tags')

        self.curs.execute('CREATE TABLE l2t_saved_query ('
                          'name TEXT, query TEXT) '
                          'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
        if self.set_status:
          self.set_status('Created table: l2t_saved_query')

        self.curs.execute('CREATE TABLE l2t_disk ('
                          'disk_type INT, mount_path TEXT, '
                          'dd_path TEXT, dd_offset TEXT, '
                          'storage_file TEXT, export_path TEXT) '
                          'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
        self.curs.execute('INSERT INTO l2t_disk ('
                          'disk_type, mount_path, dd_path, '
                          'dd_offset, storage_file, '
                          'export_path) VALUES '
                          '(0, "", "", "", "", "")')
        if self.set_status:
          self.set_status('Created table: l2t_disk')
    except MySQLdb.Error as exception:
      raise IOError('Can\'t insert to database, '
                    '[%s]', exception)

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
          self.set_status('Created index: %s' % fn)

    # Get meta info and save into their tables.
    if self.set_status:
      self.set_status('Creating metadata...')

    for field in self.META_FIELDS:
      vals = self._GetDistinctValues(field)
      self.curs.execute('DELETE FROM l2t_%ss' % field)
      for name, freq in vals.items():
        self.curs.execute(
            'INSERT INTO l2t_%ss (%ss, frequency) VALUES("%s", %s) ' % (
                field, field, name, freq))
    self.curs.execute('DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self.curs.execute("INSERT INTO l2t_tags (tag) VALUES ('%s')" % tag)

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
      if row[0] != '':
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


  def EventBody(self, event_object):
    """Formats data as 4n6time database table format and writes to the db.

    Args:
      event_object: The event object (EventObject).

    Raises:
      raise errors.NoFormatterFound: If no formatter for this event is found.
    """

    if not hasattr(event_object, 'timestamp'):
      return

    formatter = eventdata.EventFormatterManager.GetFormatter(event_object)
    if not formatter:
      raise errors.NoFormatterFound(
          'Unable to output event, no formatter found.')

    if (isinstance(
      formatter, formatters.winreg.WinRegistryGenericFormatter) and
        formatter.FORMAT_STRING.find('<|>') == -1):
      formatter.FORMAT_STRING = u'[{keyname}]<|>{text}<|>'
    elif isinstance(formatter, eventdata.ConditionalEventFormatter):
      formatter.FORMAT_STRING_SEPARATOR = u'<|>'
    elif isinstance(formatter, eventdata.EventFormatter):
      formatter.format_string = formatter.format_string.replace('}', '}<|>')
    msg, msg_short = formatter.GetMessages(event_object)
    source_short, source_long = formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self.zone)
    if not date_use:
      logging.error(u'Unable to process date for entry: %s', msg)
      return
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

    date_use_string = '{0}-{1}-{2} {3}:{4}:{5}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    tags = []
    if hasattr(event_object, 'tag'):
      tags = event_object.tag.tags
    taglist = ','.join(tags)
    row = (str(self.zone),
           helper.GetLegacy(event_object),
           source_short,
           source_long,
           getattr(event_object, 'timestamp_desc', '-'),
           getattr(event_object, 'username', '-'),
           getattr(event_object, 'hostname', '-'),
           msg,
           getattr(event_object, 'filename', '-'),
           inode,
           getattr(event_object, 'notes', '-'),
           getattr(event_object, 'parser', '-'),
           extra,
           date_use_string,
           '',
           '',
           taglist,
           '',
           getattr(event_object, 'offset', 0),
           event_object.store_number,
           event_object.store_index,
           self.GetVSSNumber(event_object),
           getattr(event_object, 'url', '-'),
           getattr(event_object, 'record_number', 0),
           getattr(event_object, 'event_identifier', '-'),
           getattr(event_object, 'event_type', '-'),
           getattr(event_object, 'source_name', '-'),
           getattr(event_object, 'user_sid', '-'),
           getattr(event_object, 'computer_name', '-'),
           self.evidence)
          
    try:
      self.curs.execute(
          'INSERT INTO log2timeline(timezone, MACB, source, '
          'sourcetype, type, user, host, description, filename, '
          'inode, notes, format, extra, datetime, reportnotes, '
          'inreport, tag, color, offset, store_number, '
          'store_index, vss_store_number, URL, record_number, '
          'event_identifier, event_type, source_name, user_sid, '
          'computer_name, evidence) VALUES ('
          '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '
          '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '
          '%s, %s, %s, %s)', row)
    except MySQLdb.Error as exception:
      logging.warning(
        u'Error appending to Database [%s].', exception)

    self.count += 1

    # TODO: Experiment if committing the current transaction
    # every 10000 inserts is the optimal approach.
    if self.count % 10000 == 0:
      self.conn.commit()
      if self.set_status:
        self.set_status('Inserting event: %s' % self.count)

  def GetVSSNumber(self, event_object):
    """Return the vss_store_number of the event."""
    if not hasattr(event_object, 'pathspec'):
      return -1

    return getattr(event_object.pathspec, 'vss_store_number', -1)
