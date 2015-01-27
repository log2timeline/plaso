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
import os
import re
import sys

import sqlite3

from plaso import formatters
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.lib import utils
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class SQLite4n6OutputFormatter(interface.LogOutputFormatter):
  """Saves the data in a SQLite database, used by the tool 4n6Time."""

  NAME = u'sql4n6'
  DESCRIPTION = (
      u'Saves the data in a SQLite database, used by the tool 4n6Time.')

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  META_FIELDS = [
      'sourcetype', 'source', 'user', 'host', 'MACB', 'color', 'type',
      'record_number']

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
    super(SQLite4n6OutputFormatter, self).__init__(
        store, filehandle, config, filter_use)
    # TODO: move this to an output module interface.
    self.set_status = getattr(config, 'set_status', None)

    # TODO: Revisit handling this outside of plaso.
    self.dbname = filehandle
    self.evidence = getattr(config, 'evidence', '-')
    self.append = getattr(config, 'append', False)
    self.fields = getattr(config, 'fields', [
        'host', 'user', 'source', 'sourcetype', 'type', 'datetime', 'color'])

  # Override LogOutputFormatter methods so it won't write to the file
  # handle any more.
  def Start(self):
    """Connect to the database and create the table before inserting."""
    if self.filehandle == sys.stdout:
      raise IOError(
          u'Unable to connect to stdout as database, please specify a file.')

    if (not self.append) and os.path.isfile(self.filehandle):
      raise IOError((
          u'Unable to use an already existing file for output '
          u'[{0:s}]').format(self.filehandle))

    self.conn = sqlite3.connect(self.dbname)
    self.conn.text_factory = str
    self.curs = self.conn.cursor()

    # Create table in database.
    if not self.append:
      self.curs.execute(
          ('CREATE TABLE log2timeline (timezone TEXT, '
           'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, '
           'user TEXT, host TEXT, description TEXT, filename TEXT, '
           'inode TEXT, notes TEXT, format TEXT, extra TEXT, '
           'datetime datetime, reportnotes TEXT, '
           'inreport TEXT, tag TEXT, color TEXT, offset INT,'
           'store_number INT, store_index INT, vss_store_number INT,'
           'url TEXT, record_number TEXT, event_identifier TEXT, '
           'event_type TEXT, source_name TEXT, user_sid TEXT, '
           'computer_name TEXT, evidence TEXT)'))
      if self.set_status:
        self.set_status('Created table: log2timeline')

      for field in self.META_FIELDS:
        self.curs.execute(
            'CREATE TABLE l2t_{0}s ({0}s TEXT, frequency INT)'.format(field))
        if self.set_status:
          self.set_status('Created table: l2t_{0:s}'.format(field))

      self.curs.execute('CREATE TABLE l2t_tags (tag TEXT)')
      if self.set_status:
        self.set_status('Created table: l2t_tags')

      self.curs.execute('CREATE TABLE l2t_saved_query (name TEXT, query TEXT)')
      if self.set_status:
        self.set_status('Created table: l2t_saved_query')

      self.curs.execute('CREATE TABLE l2t_disk (disk_type INT, mount_path TEXT,'
                        ' dd_path TEXT, dd_offset TEXT, storage_file TEXT,'
                        ' export_path TEXT)')
      self.curs.execute('INSERT INTO l2t_disk (disk_type, mount_path, dd_path,'
                        'dd_offset, storage_file, export_path) VALUES '
                        '(0, "", "", "", "", "")')
      if self.set_status:
        self.set_status('Created table: l2t_disk')

    self.count = 0

  def End(self):
    """Create indices and commit the transaction."""
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self.append:
      for field_name in self.fields:
        sql = 'CREATE INDEX {0}_idx ON log2timeline ({0})'.format(field_name)
        self.curs.execute(sql)
        if self.set_status:
          self.set_status('Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self.set_status:
      self.set_status('Creating metadata...')

    for field in self.META_FIELDS:
      vals = self._GetDistinctValues(field)
      self.curs.execute('DELETE FROM l2t_{0:s}s'.format(field))
      for name, freq in vals.items():
        self.curs.execute((
            'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
            'VALUES("{2:s}", {3:d}) ').format(field, field, name, freq))
    self.curs.execute('DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self.curs.execute('INSERT INTO l2t_tags (tag) VALUES (?)', [tag])

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

  def StartEvent(self):
    """Do nothing, just override the parent's StartEvent method."""
    pass

  def EndEvent(self):
    """Do nothing, just override the parent's EndEvent method."""
    pass

  def EventBody(self, event_object):
    """Formats data as the 4n6time table format and writes it to the database.

    Args:
      event_object: The event object (EventObject).

    Raises:
      raise errors.NoFormatterFound: If no event formatter was found.
    """
    if 'timestamp' not in event_object.GetAttributes():
      return

    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          'Unable to output event, no event formatter found.')

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

    date_use_string = u'{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    tags = []
    if hasattr(event_object, 'tag'):
      if hasattr(event_object.tag, 'tags'):
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
           GetVSSNumber(event_object),
           getattr(event_object, 'url', '-'),
           getattr(event_object, 'record_number', 0),
           getattr(event_object, 'event_identifier', '-'),
           getattr(event_object, 'event_type', '-'),
           getattr(event_object, 'source_name', '-'),
           getattr(event_object, 'user_sid', '-'),
           getattr(event_object, 'computer_name', '-'),
           self.evidence
          )

    self.curs.execute(
        ('INSERT INTO log2timeline(timezone, MACB, source, '
         'sourcetype, type, user, host, description, filename, '
         'inode, notes, format, extra, datetime, reportnotes, inreport,'
         'tag, color, offset, store_number, store_index, vss_store_number,'
         'URL, record_number, event_identifier, event_type,'
         'source_name, user_sid, computer_name, evidence)'
         ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,'
         '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'), row)

    self.count += 1

    # Commit the current transaction every 10000 inserts.
    if self.count % 10000 == 0:
      self.conn.commit()
      if self.set_status:
        self.set_status('Inserting event: {0:d}'.format(self.count))


def GetVSSNumber(event_object):
  """Return the vss_store_number of the event."""
  if not hasattr(event_object, 'pathspec'):
    return -1

  return getattr(event_object.pathspec, 'vss_store_number', -1)


manager.OutputManager.RegisterOutput(SQLite4n6OutputFormatter)
