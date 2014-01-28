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
"""This file contains a SQLite parser."""

import logging
import os
import tempfile

from plaso.lib import errors
from plaso.lib import plugin

import pytz
import sqlite3


class SQLiteCache(plugin.BasePluginCache):
  """A cache storing query results for SQLite plugins."""

  def CacheQueryResults(
      self, sql_results, attribute_name, key_name, values):
    """Build a dict object based on a SQL command.

    This function will take a SQL command, execute it and for
    each resulting row it will store a key in a dictionary.

    An example:
      sql_results = A SQL result object after executing the
                    SQL command: 'SELECT foo, bla, bar FROM my_table'
      attribute_name = 'all_the_things'
      key_name = 'foo'
      values = ['bla', 'bar']

    Results from running this against the database:
      'first', 'stuff', 'things'
      'second', 'another stuff', 'another thing'

    This will result in a dict object being created in the
    cache, called 'all_the_things' and it will contain the following value:

      all_the_things = {
          'first': ['stuff', 'things'],
          'second': ['another_stuff', 'another_thing']}

    Args:
      sql_results: The SQL result object (sqlite.Cursor) after executing
                   a SQL command on the database.
      attribute_name: The attribute name in the cache to store
                      results to. This will be the name of the
                      dict attribute.
      key_name: The name of the result field that should be used
                as a key in the resulting dict that is created.
      values: A list of result fields that are stored as values
              to the dict. If this list has only one value in it
              the value will be stored directly, otherwise the value
              will be a list containing the extracted results based
              on the names provided in this list.
    """
    setattr(self, attribute_name, {})
    attribute = getattr(self, attribute_name)

    row = sql_results.fetchone()
    while row:
      if len(values) == 1:
        attribute[row[key_name]] = row[values[0]]
      else:
        attribute[row[key_name]] = []
        for value in values:
          attribute[row[key_name]].append(row[value])

      row = sql_results.fetchone()


class SQLitePlugin(plugin.BasePlugin):
  """A SQLite plugin for Plaso."""

  __abstract = True

  NAME = 'sqlite'

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # List of tables that should be present in the database, for verification.
  REQUIRED_TABLES = frozenset([])

  def __init__(self, pre_obj):
    """Initialize the database plugin."""
    super(SQLitePlugin, self).__init__(pre_obj)
    self.db = None
    self.zone = getattr(self._knowledge_base, 'zone', pytz.utc)

  def Process(self, cache=None, database=None, **kwargs):
    """Determine if this is the right plugin for this database.

    This function takes a SQLiteDatabase object and compares the list
    of required tables against the available tables in the database.
    If all the tables defined in REQUIRED_TABLES are present in the
    database then this plugin is considered to be the correct plugin
    and the function will return back a generator that yields event
    objects.

    Args:
      cache: A SQLiteCache object.
      database: A SQLiteDatabase object.

    Returns:
      A generator that yields event objects.

    Raises:
      errors.WrongPlugin: If the database does not contain all the tables
      defined in the REQUIRED_TABLES set.
      ValueError: If the database attribute is not passed in.
    """
    if database is None:
      raise ValueError(u'Database is not set.')

    if not frozenset(database.tables) >= self.REQUIRED_TABLES:
      raise errors.WrongPlugin(
          u'Not the correct database tables for: {}'.format(
              self.plugin_name))

    super(SQLitePlugin, self).Process(**kwargs)

    self.db = database
    return self.GetEntries(cache)

  def GetEntries(self, cache=None):
    """Yields EventObjects extracted from a SQLite database."""
    for query, action in self.QUERIES:
      try:
        call_back = getattr(self, action, self.Default)
        cursor = self.db.cursor
        sql_results = cursor.execute(query)
        row = sql_results.fetchone()
        while row:
          event_generator = call_back(row=row, cache=cache)
          if event_generator:
            for event_object in event_generator:
              event_object.query = query
              if not hasattr(event_object, 'offset'):
                if 'id' in row.keys():
                  event_object.offset = row['id']
                else:
                  event_object.offset = 0
              yield event_object
          row = sql_results.fetchone()
      except sqlite3.DatabaseError as e:
        logging.debug('SQLite error occured: %s', e)

  def Default(self, unused_row, unused_cache):
    """Default callback method for SQLite events, does nothing."""
    logging.debug('Default handler: {0:s}'.format(unused_row))


class SQLiteDatabase(object):
  """A simple wrapper for opening up a SQLite database."""

  # Magic value for a SQLite database.
  MAGIC = 'SQLite format 3'

  _READ_BUFFER_SIZE = 65536

  def __init__(self, file_entry):
    """Initializes the database object.

    Args:
      file_enty: the file entry object.
    """
    self._file_entry = file_entry
    self._temp_file_name = ''
    self._open = False
    self._database = None
    self._cursor = None
    self._tables = []

  @property
  def tables(self):
    """Returns a list of all the tables in the database."""
    if not self._open:
      self.Open()

    return self._tables

  @property
  def cursor(self):
    """Returns a cursor object from the database."""
    if not self._open:
      self.Open()

    return self._database.cursor()

  def Open(self):
    """Opens up a database connection and build a list of table names."""
    file_object = self._file_entry.Open()

    # TODO: Remove this when the classifier gets implemented
    # and used. As of now, there is no check made against the file
    # to verify it's signature, thus all files are sent here, meaning
    # that this method assumes everything is a SQLite file and starts
    # copying the content of the file into memory, which is not good
    # for very large files.
    file_object.seek(0, os.SEEK_SET)

    data = file_object.read(len(self.MAGIC))

    if data != self.MAGIC:
      file_object.close()
      raise IOError(
          u'File {} not a SQLite database. (invalid signature)'.format(
              self._file_entry.name))

    # TODO: Current design copies the entire file into a buffer
    # that is parsed by each SQLite parser. This is not very efficient,
    # especially when many SQLite parsers are ran against a relatively
    # large SQLite database. This temporary file that is created should
    # be usable by all SQLite parsers so the file should only be read
    # once in memory and then deleted when all SQLite parsers have completed.

    # TODO: Change this into a proper implementation using APSW
    # and virtual filesystems when that will be available.
    # Info: http://apidoc.apsw.googlecode.com/hg/vfs.html#vfs and
    # http://apidoc.apsw.googlecode.com/hg/example.html#example-vfs
    # Until then, just copy the file into a tempfile and parse it.

    # Note that data is filled here with the file header data and
    # that with will explicityly close the temporary files and thus
    # making sure it is available for sqlite3.connect().
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
      self._temp_file_name = temp_file.name
      while data:
        temp_file.write(data)
        data = file_object.read(self._READ_BUFFER_SIZE)

    self._database = sqlite3.connect(self._temp_file_name)
    try:
      self._database.row_factory = sqlite3.Row
      self._cursor = self._database.cursor()
    except sqlite3.DatabaseError as e:
      logging.debug(u'SQLite error occured: {0:s} in file {1:s}'.format(
          e, self._file_entry.name))
      raise

    # Verify the table by reading in all table names and compare it to
    # the list of required tables.
    try:
      sql_results = self._cursor.execute(
          'SELECT name FROM sqlite_master WHERE type="table"')
    except sqlite3.DatabaseError as e:
      logging.debug(u'SQLite error occured: <{0:s}> in file {1:s}'.format(
          e, self._file_entry.name))
      raise

    self._tables = []
    for row in sql_results:
      self._tables.append(row[0])

    self._open = True

  def Close(self):
    """Close the database connection and clean up the temporary file."""
    if not self._open:
      return

    self._database.close()

    try:
      os.remove(self._temp_file_name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: {0:s} [derived from {1:s} '
          u'due to: {2:s}'.format(
              self._temp_file_name, self._file_entry.name, e))

    self._tables = []
    self._database = None
    self._temp_file_name = ''
    self._open = False

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self
