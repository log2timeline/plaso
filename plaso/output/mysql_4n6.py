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

import logging
import re
import sys

import MySQLdb

from plaso import formatters
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import output
from plaso.lib import timelib
from plaso.lib import utils
from plaso.output import helper


__author__ = 'David Nides (david.nides@gmail.com)'


class Mysql4n6(output.LogOutputFormatter):
  """Contains functions for outputting as 4n6time MySQL database."""

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  META_FIELDS = ['sourcetype', 'source', 'user', 'host', 'MACB',
                 'color', 'type', 'record_number']

  ARGUMENTS = [
      ('--db_user', {
          'dest': 'db_user',
          'type': unicode,
          'help': 'Defines the database user.',
          'metavar': 'USERNAME',
          'action': 'store',
          'default': 'root'}),
      ('--db_host', {
          'dest': 'db_host',
          'metavar': 'HOSTNAME',
          'type': unicode,
          'help': (
              'Defines the IP address or the hostname of the database '
              'server.'),
          'action': 'store',
          'default': 'localhost'}),
      ('--db_pass', {
          'dest': 'db_pass',
          'metavar': 'PASSWORD',
          'type': unicode,
          'help': 'The password for the database user.',
          'action': 'store',
          'default': 'forensic'}),
      ('--db_name', {
          'dest': 'db_name',
          'type': unicode,
          'help': 'The name of the database to connect to.',
          'action': 'store',
          'default': 'log2timeline'}),
      ('--append', {
          'dest': 'append',
          'action': 'store_true',
          'help': (
              'Defines whether the intention is to append to an already '
              'existing database or overwrite it. Defaults to overwrite.'),
          'default': False}),
      ('--fields', {
          'dest': 'fields',
          'action': 'store',
          'type': unicode,
          'nargs': '*',
          'help': 'Defines which fields should be indexed in the database.',
          'default': [
              'host', 'user', 'source', 'sourcetype', 'type', 'datetime',
              'color']}),
      ('--evidence', {
          'dest': 'evidence',
          'action': 'store',
          'help': (
              'Set the evidence field to a specific value, defaults to '
              'empty.'),
          'type': unicode,
          'default': '-'})]

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
    # TODO: move this to an output module interface.
    self._formatters_manager = formatters_manager.EventFormatterManager

    self.set_status = getattr(config, 'set_status', None)

    self.host = getattr(config, 'db_host', 'localhost')
    self.user = getattr(config, 'db_user', 'root')
    self.password = getattr(config, 'db_pass', 'forensic')
    self.dbname = getattr(config, 'db_name', 'log2timeline')
    self.evidence = getattr(config, 'evidence', '-')
    self.append = getattr(config, 'append', False)
    self.fields = getattr(config, 'fields', [
        'host', 'user', 'source', 'sourcetype', 'type', 'datetime', 'color'])

  def Start(self):
    """Connect to the database and create the table before inserting."""
    if self.dbname == '':
      raise IOError(u'Specify a database name.')

    try:
      if self.append:
        self.conn = MySQLdb.connect(self.host, self.user,
                                    self.password, self.dbname)
        self.curs = self.conn.cursor()
      else:
        self.conn = MySQLdb.connect(self.host, self.user, self.password)
        self.curs = self.conn.cursor()

      self.conn.set_character_set(u'utf8')
      self.curs.execute(u'SET NAMES utf8')
      self.curs.execute(u'SET CHARACTER SET utf8')
      self.curs.execute(u'SET character_set_connection=utf8')
      self.curs.execute(u'SET GLOBAL innodb_large_prefix=ON')
      self.curs.execute(u'SET GLOBAL innodb_file_format=barracuda')
      self.curs.execute(u'SET GLOBAL innodb_file_per_table=ON')
      self.curs.execute(
          u'CREATE DATABASE IF NOT EXISTS {0:s}'.format(self.dbname))
      self.curs.execute(u'USE {0:s}'.format(self.dbname))
      # Create tables.
      self.curs.execute(
          (u'CREATE TABLE IF NOT EXISTS log2timeline ('
           u'rowid INT NOT NULL AUTO_INCREMENT, timezone VARCHAR(256), '
           u'MACB VARCHAR(256), source VARCHAR(256), sourcetype VARCHAR(256), '
           u'type VARCHAR(256), user VARCHAR(256), host VARCHAR(256), '
           u'description TEXT, filename VARCHAR(256), inode VARCHAR(256), '
           u'notes VARCHAR(256), format VARCHAR(256), '
           u'extra TEXT, datetime datetime, reportnotes VARCHAR(256), '
           u'inreport VARCHAR(256), tag VARCHAR(256), color VARCHAR(256), '
           u'offset INT, store_number INT, store_index INT, '
           u'vss_store_number INT, URL TEXT, '
           u'record_number VARCHAR(256), event_identifier VARCHAR(256), '
           u'event_type VARCHAR(256), source_name VARCHAR(256), '
           u'user_sid VARCHAR(256), computer_name VARCHAR(256), '
           u'evidence VARCHAR(256), '
           u'PRIMARY KEY (rowid)) ENGINE=InnoDB ROW_FORMAT=COMPRESSED'))
      if self.set_status:
        self.set_status(u'Created table: log2timeline')

      for field in self.META_FIELDS:
        self.curs.execute(
            u'CREATE TABLE IF NOT EXISTS l2t_{0}s ({0}s TEXT, frequency INT) '
            u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED'.format(field))
        if self.set_status:
          self.set_status(u'Created table: l2t_{0:s}'.format(field))

      self.curs.execute(
          u'CREATE TABLE IF NOT EXISTS l2t_tags (tag TEXT) '
          u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      if self.set_status:
        self.set_status(u'Created table: l2t_tags')

      self.curs.execute(
          u'CREATE TABLE IF NOT EXISTS l2t_saved_query ('
          u'name TEXT, query TEXT) '
          u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      if self.set_status:
        self.set_status(u'Created table: l2t_saved_query')

      self.curs.execute(
          u'CREATE TABLE IF NOT EXISTS l2t_disk ('
          u'disk_type INT, mount_path TEXT, '
          u'dd_path TEXT, dd_offset TEXT, '
          u'storage_file TEXT, export_path TEXT) '
          u'ENGINE=InnoDB ROW_FORMAT=COMPRESSED')
      self.curs.execute(
          u'INSERT INTO l2t_disk ('
          u'disk_type, mount_path, dd_path, '
          u'dd_offset, storage_file, '
          u'export_path) VALUES '
          u'(0, "", "", "", "", "")')
      if self.set_status:
        self.set_status(u'Created table: l2t_disk')
    except MySQLdb.Error as exception:
      raise IOError(u'Unable to insert into database with error: {0:s}'.format(
          exception))

    self.count = 0

  def End(self):
    """Create indices and commit the transaction."""
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for field_name in self.fields:
        sql = u'CREATE INDEX {0}_idx ON log2timeline ({0:s})'.format(field_name)
        self.curs.execute(sql)
        if self.set_status:
          self.set_status(u'Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self.set_status:
      self.set_status(u'Creating metadata...')

    for field in self.META_FIELDS:
      vals = self._GetDistinctValues(field)
      self.curs.execute(u'DELETE FROM l2t_{0:s}s'.format(field))
      for name, freq in vals.items():
        self.curs.execute((
            u'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
            u'VALUES("{2:s}", {3:d}) ').format(field, field, name, freq))

    self.curs.execute(u'DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self.curs.execute(
          u'INSERT INTO l2t_tags (tag) VALUES ("{0:s}")'.format(tag))

    if self.set_status:
      self.set_status(u'Database created.')

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
        u'SELECT DISTINCT tag FROM log2timeline')

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

    event_formatter = self._formatters_manager.GetFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to output event, no event formatter found.')

    if (isinstance(
        event_formatter, formatters.winreg.WinRegistryGenericFormatter) and
        event_formatter.FORMAT_STRING.find('<|>') == -1):
      event_formatter.FORMAT_STRING = u'[{keyname}]<|>{text}<|>'

    elif isinstance(
        event_formatter, formatters_interface.ConditionalEventFormatter):
      event_formatter.FORMAT_STRING_SEPARATOR = u'<|>'

    elif isinstance(event_formatter, formatters_interface.EventFormatter):
      event_formatter.format_string = event_formatter.format_string.replace(
          '}', '}<|>')

    msg, _ = event_formatter.GetMessages(event_object)
    source_short, source_long = event_formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self.zone)
    if not date_use:
      logging.error(u'Unable to process date for entry: {0:s}'.format(msg))
      return
    extra = []
    format_variables = self.FORMAT_ATTRIBUTE_RE.findall(
        event_formatter.format_string)
    for key in event_object.GetAttributes():
      if key in utils.RESERVED_VARIABLES or key in format_variables:
        continue
      extra.append(u'{0:s}: {1!s} '.format(
          key, getattr(event_object, key, None)))

    extra = u' '.join(extra)

    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if (hasattr(event_object, 'pathspec') and
          hasattr(event_object.pathspec, 'image_inode')):
        inode = event_object.pathspec.image_inode

    date_use_string = u'{0:d}-{1:d}-{2:d} {3:d}:{4:d}:{5:d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    tags = []
    if hasattr(event_object, 'tag') and hasattr(event_object.tag, 'tags'):
      tags = event_object.tag.tags
    else:
      tags = u''

    taglist = u','.join(tags)
    row = (
        str(self.zone),
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
          u'Unable to insert into database with error: {0:s}.'.format(
              exception))

    self.count += 1

    # TODO: Experiment if committing the current transaction
    # every 10000 inserts is the optimal approach.
    if self.count % 10000 == 0:
      self.conn.commit()
      if self.set_status:
        self.set_status(u'Inserting event: {0:d}'.format(self.count))

  def GetVSSNumber(self, event_object):
    """Return the vss_store_number of the event."""
    if not hasattr(event_object, 'pathspec'):
      return -1

    return getattr(event_object.pathspec, 'vss_store_number', -1)
