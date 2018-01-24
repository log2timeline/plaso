# -*- coding: utf-8 -*-
"""The SQLite parser plugin interface."""

from __future__ import unicode_literals

import logging

# pylint: disable=wrong-import-order
try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3

from plaso.parsers import plugins


class SQLitePlugin(plugins.BasePlugin):
  """SQLite parser plugin."""

  NAME = 'sqlite'
  DESCRIPTION = 'Parser for SQLite database files.'

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # List of tables that should be present in the database, for verification.
  REQUIRED_TABLES = frozenset([])

  # Database schemas this plugin was originally designed for.
  # Should be a list of dictionaries with {table_name: SQLCommand} format.
  SCHEMAS = []

  def __init__(self):
    """Initializes a SQLite parser plugin."""
    super(SQLitePlugin, self).__init__()
    self._keys_per_query = {}

  def _GetRowValue(self, query_hash, row, value_name):
    """Retrieves a value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      object: value.
    """
    keys_name_to_index_map = self._keys_per_query.get(query_hash, None)
    if not keys_name_to_index_map:
      keys_name_to_index_map = {
          name: index for index, name in enumerate(row.keys())}
      self._keys_per_query[query_hash] = keys_name_to_index_map

    value_index = keys_name_to_index_map.get(value_name)

    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    return row[value_index]

  @classmethod
  def _HashRow(cls, row):
    """Hashes the given row.

    Args:
      row (sqlite3.Row): row.

    Returns:
      int: hash value of the given row.
    """
    hash_value = 0
    for column_value in row:
      try:
        column_hash_value = hash(column_value)
      except TypeError:
        # In Python 2, blobs are "read-write buffer" and will cause a
        # "writable buffers are not hashable" TypeError exception if we try
        # to hash it. Therefore, we will turn it into a string beforehand.
        # Since Python 3 does not support the buffer type we cannot check
        # the type of column_value.
        column_hash_value = hash(str(column_value))

      hash_value ^= column_hash_value
    return hash_value

  def _ParseQuery(
      self, parser_mediator, database, query, callback, row_cache, cache=None):
    """Queries a database and parses the results.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database (SQLiteDatabase): database.
      query (str): query.
      callback (function): function to invoke to parse an individual row.
      row_cache (set): hashes of the rows that have been parsed.
      cache (Optional[SQLiteCache]): cache.
    """
    try:
      rows = database.Query(query)

    except sqlite3.DatabaseError as exception:
      parser_mediator.ProduceExtractionError(
          'unable to run query: {0:s} on database with error: {1!s}'.format(
              query, exception))
      return

    for index, row in enumerate(rows):
      if parser_mediator.abort:
        break

      try:
        callback(
            parser_mediator, query, row, cache=cache, database=database)

        row_hash = self._HashRow(row)
        row_cache.add(row_hash)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionError((
            'unable to parse row: {0:d} with callback: {1:s} on database '
            'with error: {2!s}').format(
                index, callback.__name__, exception))
        # TODO: consider removing return.
        return

  def _ParseQueryWithWAL(
      self, parser_mediator, database_wal, query, callback, row_cache,
      cache=None):
    """Queries a database with WAL and parses the results.

    Note that cached rows will be ignored.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database_wal (SQLiteDatabase): database with WAL.
      query (str): query.
      callback (function): function to invoke to parse an individual row.
      row_cache (set): hashes of the rows that have been parsed.
      cache (Optional[SQLiteCache]): cache.
    """
    try:
      rows = database_wal.Query(query)

    except sqlite3.DatabaseError as exception:
      parser_mediator.ProduceExtractionError((
          'unable to run query: {0:s} on database with WAL with error: '
          '{1!s}').format(query, exception))
      return

    for index, row in enumerate(rows):
      if parser_mediator.abort:
        break

      row_hash = self._HashRow(row)
      if row_hash in row_cache:
        continue

      try:
        callback(
            parser_mediator, query, row, cache=cache, database=database_wal)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionError((
            'unable to parse row: {0:d} with callback: {1:s} on database '
            'with WAL with error: {2!s}').format(
                index, callback.__name__, exception))
        # TODO: consider removing return.
        return

  def GetEntries(
      self, parser_mediator, cache=None, database=None, database_wal=None,
      wal_file_entry=None, **unused_kwargs):
    """Extracts events from a SQLite database.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
      database_wal (Optional[SQLiteDatabase]): database object with WAL file
          committed.
      wal_file_entry (Optional[dfvfs.FileEntry]): file entry for the database
          with WAL file committed.
    """
    schema_match = False
    wal_schema_match = False
    for schema in self.SCHEMAS:
      if database and database.schema == schema:
        schema_match = True
      if database_wal and database_wal.schema == schema:
        wal_schema_match = True

    for query, callback_method in self.QUERIES:
      if parser_mediator.abort:
        break

      callback = getattr(self, callback_method, None)
      if callback is None:
        logging.warning(
            '[{0:s}] missing callback method: {1:s} for query: {2:s}'.format(
                self.NAME, callback_method, query))
        continue

      row_cache = set()

      if database:
        try:
          parser_mediator.AddEventAttribute('schema_match', schema_match)

          self._ParseQuery(
              parser_mediator, database, query, callback, row_cache,
              cache=cache)

        finally:
          parser_mediator.RemoveEventAttribute('schema_match')

      if database_wal:
        file_entry = parser_mediator.GetFileEntry()

        try:
          parser_mediator.AddEventAttribute('schema_match', wal_schema_match)
          parser_mediator.SetFileEntry(wal_file_entry)

          self._ParseQueryWithWAL(
              parser_mediator, database_wal, query, callback, row_cache,
              cache=cache)

        finally:
          parser_mediator.RemoveEventAttribute('schema_match')
          parser_mediator.SetFileEntry(file_entry)

  # pylint: disable=arguments-differ
  def Process(
      self, parser_mediator, cache=None, database=None, database_wal=None,
      wal_file_entry=None, **kwargs):
    """Determine if this is the right plugin for this database.

    This function takes a SQLiteDatabase object and compares the list
    of required tables against the available tables in the database.
    If all the tables defined in REQUIRED_TABLES are present in the
    database then this plugin is considered to be the correct plugin
    and the function will return back a generator that yields event
    objects.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.
      database_wal (Optional[SQLiteDatabase]): database with its
          Write-Ahead Log (WAL) committed.
      wal_file_entry (Optional[dfvfs.FileEntry]): file entry of the database
          with is Write-Ahead Log (WAL) committed.

    Raises:
      ValueError: If the database attribute is not passed in.
    """
    if database is None:
      raise ValueError('Database is not set.')

    # This will raise if unhandled keyword arguments are passed.
    super(SQLitePlugin, self).Process(parser_mediator)

    self.GetEntries(
        parser_mediator, cache=cache, database=database,
        database_wal=database_wal, wal_file_entry=wal_file_entry)
