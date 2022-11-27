# -*- coding: utf-8 -*-
"""Interface for SQLite database file parser plugins."""

import sqlite3

from plaso.parsers import logger
from plaso.parsers import plugins


class SQLitePlugin(plugins.BasePlugin):
  """SQLite parser plugin."""

  NAME = 'sqlite_plugin'
  DATA_FORMAT = 'SQLite database file'

  # Dictionary of frozensets containing the columns in tables that must be
  # present in the database for the plugin to run.
  # This generally should only include tables/columns that are used in SQL
  # queries by the plugin and not include extraneous tables/columns to better
  # accommodate future application database versions. The exception to this is
  # when extra tables/columns are needed to identify the target database from
  # others with a similar structure.
  REQUIRED_STRUCTURE = {}

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # Database schemas this plugin was originally designed for.
  # Should be a list of dictionaries with {table_name: SQLCommand} format.
  SCHEMAS = []

  # Value to indicate the schema of the database must match one of the schemas
  # defined by the plugin.
  REQUIRES_SCHEMA_MATCH = False

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
      object: value or None if not available.
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
    values = []
    for value in row:
      try:
        value = '{0!s}'.format(value)
      except UnicodeDecodeError:
        # In Python 2, blobs are "read-write buffer" and will cause a
        # UnicodeDecodeError exception if we try format it as a string.
        # Since Python 3 does not support the buffer type we cannot check
        # the type of value.
        value = repr(value)

      values.append(value)

    return hash(' '.join(values))

  def _ParseSQLiteDatabase(
      self, parser_mediator, database, query, callback, cache):
    """Extracts events from a SQLite database.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database (SQLiteDatabase): database.
      query (str): query.
      callback (function): function to invoke to parse an individual row.
      cache (SQLiteCache): cache.
    """
    row_cache = cache.GetRowCache(query)

    try:
      rows = database.Query(query)

    except sqlite3.DatabaseError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to run query: {0:s} on database with error: {1!s}'.format(
              query, exception))
      return

    for index, row in enumerate(rows):
      if parser_mediator.abort:
        break

      row_hash = self._HashRow(row)
      if row_hash in row_cache:
        continue

      try:
        callback(parser_mediator, query, row, cache=cache, database=database)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'unable to parse row: {0:d} with callback: {1:s} on database '
            'with error: {2!s}').format(
                index, callback.__name__, exception))
        # TODO: consider removing return.
        return

      row_cache.add(row_hash)

  def CheckRequiredTablesAndColumns(self, database):
    """Check if the database has the minimal structure required by the plugin.

    Args:
      database (SQLiteDatabase): the database who's structure is being checked.

    Returns:
      bool: True if the database has the required tables and columns defined by
          the plugin, or False if it does not or if the plugin does not define
          required tables and columns. The database can have more tables and/or
          columns than specified by the plugin and still return True.
    """
    if not self.REQUIRED_STRUCTURE:
      return False

    has_required_structure = True
    for required_table, required_columns in self.REQUIRED_STRUCTURE.items():
      if required_table not in database.tables:
        has_required_structure = False
        break

      if not frozenset(required_columns).issubset(
          database.columns_per_table.get(required_table)):
        has_required_structure = False
        break

    return has_required_structure

  def CheckSchema(self, database):
    """Checks the schema of a database with that defined in the plugin.

    Args:
      database (SQLiteDatabase): SQLite database to check.

    Returns:
      bool: True if the schema of the database matches that defined by
          the plugin, or False if the schemas do not match or no schema
          is defined by the plugin.
    """
    schema_match = False
    if self.SCHEMAS:
      for schema in self.SCHEMAS:
        if database and database.schema == schema:
          schema_match = True

    return schema_match

  # pylint: disable=arguments-differ
  def Process(
      self, parser_mediator, cache=None, database=None, **unused_kwargs):
    """Extracts events from a SQLite database.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.

    Raises:
      ValueError: If the database or cache value are missing.
    """
    if cache is None:
      raise ValueError('Missing cache value.')

    if database is None:
      raise ValueError('Missing database value.')

    # This will raise if unhandled keyword arguments are passed.
    super(SQLitePlugin, self).Process(parser_mediator)

    for query, callback_method in self.QUERIES:
      if parser_mediator.abort:
        break

      callback = getattr(self, callback_method, None)
      if callback is None:
        logger.warning(
            '[{0:s}] missing callback method: {1:s} for query: {2:s}'.format(
                self.NAME, callback_method, query))
        continue

      self._ParseSQLiteDatabase(
          parser_mediator, database, query, callback, cache)
