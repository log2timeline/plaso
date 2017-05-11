# -*- coding: utf-8 -*-
"""The SQLite parser plugin interface."""

import logging
import sys

# pylint: disable=wrong-import-order
try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3

from plaso.parsers import plugins


class SQLitePlugin(plugins.BasePlugin):
  """SQLite parser plugin."""

  NAME = u'sqlite'
  DESCRIPTION = u'Parser for SQLite database files.'

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # List of tables that should be present in the database, for verification.
  REQUIRED_TABLES = frozenset([])

  # Database schemas this plugin was originally designed for.
  # Should be a list of dictionaries with {table_name: SQLCommand} format.
  SCHEMAS = []

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
      # In Python 2, blobs are "read-write buffer" and will cause a
      # "writable buffers are not hashable" error if we try to hash it.
      # Therefore, we will turn it into a string beforehand.
      if sys.version_info[0] < 3 and isinstance(column_value, buffer):
        column_value = str(column_value)
      hash_value ^= hash(column_value)
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
          u'unable to run query: {0:s} on database with error: {1!s}'.format(
              query, exception))
      return

    for index, row in enumerate(rows):
      if parser_mediator.abort:
        break

      try:
        callback(
            parser_mediator, row, cache=cache, database=database, query=query)

        row_hash = self._HashRow(row)
        row_cache.add(row_hash)

      except sqlite3.DatabaseError as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse row: {0:d} of results of query: {1:s} on '
            u'database with error: {2!s}').format(index, query, exception))
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
          u'unable to run query: {0:s} on database with WAL with error: '
          u'{1!s}').format(query, exception))
      return

    for index, row in enumerate(rows):
      if parser_mediator.abort:
        break

      row_hash = self._HashRow(row)
      if row_hash in row_cache:
        continue

      try:
        callback(
            parser_mediator, row, cache=cache, database=database_wal,
            query=query)

      except sqlite3.DatabaseError as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse row: {0:d} of results of query: {1:s} on '
            u'database with WAL with error: {2!s}').format(
                index, query, exception))
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
          commited.
      wal_file_entry (Optional[dfvfs.FileEntry]): file entry for the database
          with WAL file commited.
    """
    schema_match = None
    if database:
      schema_match = any(schema == database.schema for schema in self.SCHEMAS)

    wal_schema_match = None
    if database_wal:
      wal_schema_match = any(
          schema == database_wal.schema for schema in self.SCHEMAS)

    for query, callback_method in self.QUERIES:
      if parser_mediator.abort:
        break

      callback = getattr(self, callback_method, None)
      if callback is None:
        logging.warning(
            u'[{0:s}] missing callback method: {1:s} for query: {2:s}'.format(
                self.NAME, callback_method, query))
        continue

      row_cache = set()

      if database:
        try:
          parser_mediator.AddEventAttribute(u'schema_match', schema_match)

          self._ParseQuery(
              parser_mediator, database, query, callback, row_cache,
              cache=cache)

        finally:
          parser_mediator.RemoveEventAttribute(u'schema_match')

      if database_wal:
        file_entry = parser_mediator.GetFileEntry()

        try:
          parser_mediator.AddEventAttribute(u'schema_match', wal_schema_match)
          parser_mediator.SetFileEntry(wal_file_entry)

          self._ParseQueryWithWAL(
              parser_mediator, database_wal, query, callback, row_cache,
              cache=cache)

        finally:
          parser_mediator.RemoveEventAttribute(u'schema_match')
          parser_mediator.SetFileEntry(file_entry)

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
      raise ValueError(u'Database is not set.')

    # This will raise if unhandled keyword arguments are passed.
    super(SQLitePlugin, self).Process(parser_mediator)

    self.GetEntries(
        parser_mediator, cache=cache, database=database,
        database_wal=database_wal, wal_file_entry=wal_file_entry)
