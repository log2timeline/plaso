# -*- coding: utf-8 -*-
"""This file contains a SQLite parser."""

import logging
import os
import tempfile

try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


class SQLiteCache(plugins.BasePluginCache):
  """A cache storing query results for SQLite plugins."""

  def CacheQueryResults(
      self, sql_results, attribute_name, key_name, column_names):
    """Build a dict object based on a SQL command.

    This function will take a SQL command, execute it and for
    each resulting row it will store a key in a dictionary.

    An example::

      sql_results = A SQL result object after executing the
                    SQL command: 'SELECT foo, bla, bar FROM my_table'
      attribute_name = 'all_the_things'
      key_name = 'foo'
      column_names = ['bla', 'bar']

    Results from running this against the database:
    'first', 'stuff', 'things'
    'second', 'another stuff', 'another thing'

    This will result in a dict object being created in the
    cache, called 'all_the_things' and it will contain the following value::

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
      column_names: A list of column names that are stored as values
                    to the dict. If this list has only one value in it
                    the value will be stored directly, otherwise the value
                    will be a list containing the extracted results based
                    on the names provided in this list.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    setattr(self, attribute_name, {})
    attribute = getattr(self, attribute_name)


    row = sql_results.fetchone()
    while row:
      key_value = row[key_name]

      if len(column_names) == 1:
        attribute[key_value] = row[column_names[0]]
      else:
        attribute[key_value] = []
        for column_name in column_names:
          column_value = row[column_name]
          attribute[key_value].append(column_value)

      row = sql_results.fetchone()


class SQLiteDatabase(object):
  """A simple wrapper for opening up a SQLite database."""

  _READ_BUFFER_SIZE = 65536

  def __init__(self, filename):
    """Initializes the database object.

    Args:
      filename: string containing the name of the file entry.
    """
    self._database = None
    self._filename = filename
    self._is_open = False
    self._table_names = []
    self._temp_file_name = u''

  @property
  def tables(self):
    """Returns a list of the names of all the tables."""
    return self._table_names

  def Close(self):
    """Close the database connection and clean up the temporary file."""
    self._table_names = []

    if self._is_open:
      self._database.close()
    self._database = None

    if os.path.exists(self._temp_file_name):
      try:
        os.remove(self._temp_file_name)
      except (OSError, IOError) as exception:
        logging.warning((
            u'Unable to remove temporary copy: {0:s} of SQLite database: '
            u'{1:s} with error: {2:s}').format(
                self._temp_file_name, self._filename, exception))

    self._temp_file_name = u''

    self._is_open = False

  def Open(self, file_object):
    """Opens a SQLite database file.

    Since pysqlite cannot read directly from a file-like object a temporary
    copy of the file is made. After creating a copy the database file this
    function sets up a connection with the database and determines the names
    of the tables.

    Args:
      file_object: the file-like object.

    Raises:
      IOError: if the file-like object cannot be read.
      sqlite3.DatabaseError: if the database cannot be parsed.
      ValueErorr: if the file-like object is missing.
    """
    if not file_object:
      raise ValueError(u'Missing file object.')

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

      try:
        data = file_object.read(self._READ_BUFFER_SIZE)
        while data:
          temp_file.write(data)
          data = file_object.read(self._READ_BUFFER_SIZE)
      except IOError:
        os.remove(self._temp_file_name)
        self._temp_file_name = u''
        raise

    self._database = sqlite3.connect(self._temp_file_name)
    try:
      self._database.row_factory = sqlite3.Row
      cursor = self._database.cursor()

      sql_results = cursor.execute(
          u'SELECT name FROM sqlite_master WHERE type="table"')

      self._table_names = [row[0] for row in sql_results]

    except sqlite3.DatabaseError as exception:
      self._database.close()
      self._database = None

      os.remove(self._temp_file_name)
      self._temp_file_name = u''

      logging.debug(
          u'Unable to parse SQLite database: {0:s} with error: {1:s}'.format(
              self._filename, exception))
      raise

    self._is_open = True

  def Query(self, query):
    """Queries the database.

    Args:
      query: string containing an SQL query.

    Returns:
      A results iterator (instance of sqlite3.Cursor).
    """
    cursor = self._database.cursor()
    cursor.execute(query)
    return cursor


class SQLiteParser(interface.FileObjectParser):
  """Parses SQLite database files."""

  NAME = u'sqlite'
  DESCRIPTION = u'Parser for SQLite database files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(SQLiteParser, self).__init__()
    self._local_zone = False
    self._plugins = SQLiteParser.GetPluginObjects()
    self.db = None

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'SQLite format 3', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a SQLite database file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()
    database = SQLiteDatabase(filename)
    try:
      database.Open(file_object)

    except (IOError, ValueError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to open database with error: {0:s}'.format(
              exception))

    except sqlite3.DatabaseError as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse SQLite database with error: {0:s}.'.format(
              exception))

    # Create a cache in which the resulting tables are cached.
    cache = SQLiteCache()
    try:
      # TODO: add a table name filter and do the plugin selection here.
      for plugin_object in self._plugins:
        try:
          plugin_object.UpdateChainAndProcess(
              parser_mediator, cache=cache, database=database)

        except errors.WrongPlugin:
          logging.debug(
              u'Plugin: {0:s} cannot parse database: {1:s}'.format(
                  plugin_object.NAME, parser_mediator.GetDisplayName()))

    finally:
      database.Close()


manager.ParsersManager.RegisterParser(SQLiteParser)
