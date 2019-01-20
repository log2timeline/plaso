# -*- coding: utf-8 -*-
"""Defines the output module for the SQLite database used by 4n6time."""

from __future__ import unicode_literals

import os

try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3

from plaso.output import manager
from plaso.output import shared_4n6time


class SQLite4n6TimeOutputModule(shared_4n6time.Shared4n6TimeOutputModule):
  """Saves the data in a SQLite database, used by the tool 4n6time."""

  NAME = '4n6time_sqlite'
  DESCRIPTION = (
      'Saves the data in a SQLite database, used by the tool 4n6time.')

  _META_FIELDS = frozenset([
      'sourcetype', 'source', 'user', 'host', 'MACB', 'type',
      'record_number'])

  _CREATE_TABLE_QUERY = (
      'CREATE TABLE log2timeline (timezone TEXT, '
      'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, '
      'user TEXT, host TEXT, description TEXT, filename TEXT, '
      'inode TEXT, notes TEXT, format TEXT, extra TEXT, '
      'datetime datetime, reportnotes TEXT, '
      'inreport TEXT, tag TEXT, offset INT, vss_store_number INT, '
      'url TEXT, record_number TEXT, event_identifier TEXT, '
      'event_type TEXT, source_name TEXT, user_sid TEXT, '
      'computer_name TEXT, evidence TEXT)')

  _INSERT_QUERY = (
      'INSERT INTO log2timeline(timezone, MACB, source, '
      'sourcetype, type, user, host, description, filename, '
      'inode, notes, format, extra, datetime, reportnotes, inreport, '
      'tag, offset, vss_store_number, URL, record_number, '
      'event_identifier, event_type, source_name, user_sid, computer_name, '
      'evidence) '
      'VALUES (:timezone, :MACB, :source, :sourcetype, :type, :user, :host, '
      ':description, :filename, :inode, :notes, :format, :extra, :datetime, '
      ':reportnotes, :inreport, :tag, :offset, :vss_store_number, '
      ':URL, :record_number, :event_identifier, :event_type, :source_name, '
      ':user_sid, :computer_name, :evidence)')

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator (OutputMediator): output mediator.

    Raises:
      ValueError: if the file handle is missing.
    """
    super(SQLite4n6TimeOutputModule, self).__init__(output_mediator)
    self._connection = None
    self._count = 0
    self._cursor = None
    self._filename = None

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types.

    Args:
      field_name (str): name of the filed to retrieve.

    Returns:
      dict[str, int]: counts of field types by name.
    """
    self._cursor.execute(
        'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
            field_name))

    result = {}
    row = self._cursor.fetchone()
    while row:
      if row[0]:
        result[row[0]] = row[1]
      row = self._cursor.fetchone()
    return result

  def _ListTags(self):
    """Query database for unique tag types."""
    all_tags = []
    self._cursor.execute('SELECT DISTINCT tag FROM log2timeline')

    # This cleans up the messy SQL return.
    tag_row = self._cursor.fetchone()
    while tag_row:
      tag_string = tag_row[0]
      if tag_string:
        tags = tag_string.split(',')
        for tag in tags:
          if tag not in all_tags:
            all_tags.append(tag)
      tag_row = self._cursor.fetchone()
    # TODO: make this method an iterator.
    return all_tags

  def Close(self):
    """Disconnects from the database.

    This method will create the necessary indices and commit outstanding
    transactions before disconnecting.
    """
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self._append:
      for field_name in self._fields:
        query = 'CREATE INDEX {0:s}_idx ON log2timeline ({0:s})'.format(
            field_name)
        self._cursor.execute(query)
        if self._set_status:
          self._set_status('Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self._set_status:
      self._set_status('Creating metadata...')

    for field in self._META_FIELDS:
      values = self._GetDistinctValues(field)
      self._cursor.execute('DELETE FROM l2t_{0:s}s'.format(field))
      for name, frequency in iter(values.items()):
        self._cursor.execute((
            'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
            'VALUES("{2:s}", {3:d}) ').format(field, field, name, frequency))
    self._cursor.execute('DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self._cursor.execute('INSERT INTO l2t_tags (tag) VALUES (?)', [tag])

    if self._set_status:
      self._set_status('Database created.')

    self._connection.commit()
    self._cursor.close()
    self._connection.close()

    self._cursor = None
    self._connection = None

  def Open(self):
    """Connects to the database and creates the required tables.

    Raises:
      IOError: if the specified output file already exists.
      OSError: if the specified output file already exists.
      ValueError: if the filename is not set.
    """
    if not self._filename:
      raise ValueError('Missing filename.')

    if not self._append and os.path.isfile(self._filename):
      raise IOError((
          'Unable to use an already existing file for output '
          '[{0:s}]').format(self._filename))

    self._connection = sqlite3.connect(self._filename)
    self._cursor = self._connection.cursor()

    # Create table in database.
    if not self._append:
      self._cursor.execute(self._CREATE_TABLE_QUERY)

      for field in self._META_FIELDS:
        query = 'CREATE TABLE l2t_{0:s}s ({0:s}s TEXT, frequency INT)'.format(
            field)
        self._cursor.execute(query)
        if self._set_status:
          self._set_status('Created table: l2t_{0:s}'.format(field))

      self._cursor.execute('CREATE TABLE l2t_tags (tag TEXT)')
      if self._set_status:
        self._set_status('Created table: l2t_tags')

      query = 'CREATE TABLE l2t_saved_query (name TEXT, query TEXT)'
      self._cursor.execute(query)
      if self._set_status:
        self._set_status('Created table: l2t_saved_query')

      query = (
          'CREATE TABLE l2t_disk (disk_type INT, mount_path TEXT, '
          'dd_path TEXT, dd_offset TEXT, storage_file TEXT, export_path TEXT)')
      self._cursor.execute(query)

      query = (
          'INSERT INTO l2t_disk (disk_type, mount_path, dd_path, dd_offset, '
          'storage_file, export_path) VALUES (0, "", "", "", "", "")')
      self._cursor.execute(query)
      if self._set_status:
        self._set_status('Created table: l2t_disk')

    self._count = 0

  def SetFilename(self, filename):
    """Sets the filename.

    Args:
      filename (str): the filename.
    """
    self._filename = filename

  def WriteEventBody(self, event):
    """Writes the body of an event to the output.

    Args:
      event (EventObject): event.
    """
    # sqlite seems to support milli seconds precision but that seems
    # not to be used by 4n6time
    row = self._GetSanitizedEventValues(event)

    self._cursor.execute(self._INSERT_QUERY, row)
    self._count += 1
    # Commit the current transaction every 10000 inserts.
    if self._count % 10000 == 0:
      self._connection.commit()
      if self._set_status:
        self._set_status('Inserting event: {0:d}'.format(self._count))


manager.OutputManager.RegisterOutput(SQLite4n6TimeOutputModule)
