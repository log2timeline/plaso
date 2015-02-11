# -*- coding: utf-8 -*-
"""This file contains a SQLite parser."""

import logging
import os
import tempfile

import sqlite3

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


class SQLiteCache(plugins.BasePluginCache):
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


class SQLiteDatabase(object):
  """A simple wrapper for opening up a SQLite database."""

  # Magic value for a SQLite database.
  MAGIC = 'SQLite format 3'

  _READ_BUFFER_SIZE = 65536

  def __init__(self, file_entry):
    """Initializes the database object.

    Args:
      file_entry: the file entry object.
    """
    self._cursor = None
    self._database = None
    self._file_entry = file_entry
    self._open = False
    self._tables = []
    self._temp_file_name = ''

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  @property
  def cursor(self):
    """Returns a cursor object from the database."""
    if not self._open:
      self.Open()

    return self._database.cursor()

  @property
  def tables(self):
    """Returns a list of all the tables in the database."""
    if not self._open:
      self.Open()

    return self._tables

  def Close(self):
    """Close the database connection and clean up the temporary file."""
    if not self._open:
      return

    self._database.close()

    try:
      os.remove(self._temp_file_name)
    except (OSError, IOError) as exception:
      logging.warning((
          u'Unable to remove temporary copy: {0:s} of SQLite database: {1:s} '
          u'with error: {2:s}').format(
              self._temp_file_name, self._file_entry.name, exception))

    self._tables = []
    self._database = None
    self._temp_file_name = ''
    self._open = False

  def Open(self):
    """Opens up a database connection and build a list of table names."""
    file_object = self._file_entry.GetFileObject()

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
          u'File {0:s} not a SQLite database. (invalid signature)'.format(
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
    # that with will explicitly close the temporary files and thus
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
    except sqlite3.DatabaseError as exception:
      logging.debug(
          u'Unable to parse SQLite database: {0:s} with error: {1:s}'.format(
              self._file_entry.name, exception))
      raise

    # Verify the table by reading in all table names and compare it to
    # the list of required tables.
    try:
      sql_results = self._cursor.execute(
          'SELECT name FROM sqlite_master WHERE type="table"')
    except sqlite3.DatabaseError as exception:
      logging.debug(
          u'Unable to parse SQLite database: {0:s} with error: {1:s}'.format(
              self._file_entry.name, exception))
      raise

    self._tables = []
    for row in sql_results:
      self._tables.append(row[0])

    self._open = True


class SQLiteParser(interface.BasePluginsParser):
  """A SQLite parser for Plaso."""

  # Name of the parser, which enables all plugins by default.
  NAME = 'sqlite'
  DESCRIPTION = u'Parser for SQLite database files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(SQLiteParser, self).__init__()
    self._local_zone = False
    self._plugins = SQLiteParser.GetPluginObjects()
    self.db = None

  def Parse(self, parser_mediator, **kwargs):
    """Parses an SQLite database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Returns:
      A event object generator (EventObjects) extracted from the database.
    """
    file_entry = parser_mediator.GetFileEntry()
    with SQLiteDatabase(file_entry) as database:
      try:
        database.Open()
      except IOError as exception:
        raise errors.UnableToParseFile(
            u'Unable to open database with error: {0:s}'.format(
                repr(exception)))
      except sqlite3.DatabaseError as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse SQLite database with error: {0:s}.'.format(
                repr(exception)))

      # Create a cache in which the resulting tables are cached.
      cache = SQLiteCache()
      for plugin_object in self._plugins:
        try:
          plugin_object.UpdateChainAndProcess(
              parser_mediator, cache=cache, database=database)
        except errors.WrongPlugin:
          logging.debug(
              u'Plugin: {0:s} cannot parse database: {1:s}'.format(
                  plugin_object.NAME, parser_mediator.GetDisplayName()))


manager.ParsersManager.RegisterParser(SQLiteParser)
