# -*- coding: utf-8 -*-
"""This file contains a SQLite parser."""

import logging

import sqlite3

from plaso.lib import errors
from plaso.parsers import plugins


class SQLitePlugin(plugins.BasePlugin):
  """A SQLite plugin for Plaso."""

  NAME = 'sqlite'
  DESCRIPTION = u'Parser for SQLite database files.'

  # Queries to be executed.
  # Should be a list of tuples with two entries, SQLCommand and callback
  # function name.
  QUERIES = []

  # List of tables that should be present in the database, for verification.
  REQUIRED_TABLES = frozenset([])

  def GetEntries(
      self, parser_mediator, cache=None, database=None, **unused_kwargs):
    """Extracts event objects from a SQLite database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cache: A SQLiteCache object.
      database: A database object (instance of SQLiteDatabase).
    """
    for query, callback_method in self.QUERIES:
      try:
        callback = getattr(self, callback_method, None)
        if callback is None:
          logging.warning(
              u'[{0:s}] missing callback method: {1:s} for query: {2:s}'.format(
                  self.NAME, callback_method, query))
          continue

        cursor = database.cursor
        sql_results = cursor.execute(query)
        row = sql_results.fetchone()

        while row:
          callback(
              parser_mediator, row, query=query, cache=cache, database=database)

          row = sql_results.fetchone()

      except sqlite3.DatabaseError as exception:
        logging.debug(u'SQLite error occurred: {0:s}'.format(exception))

  def Process(self, parser_mediator, cache=None, database=None, **kwargs):
    """Determine if this is the right plugin for this database.

    This function takes a SQLiteDatabase object and compares the list
    of required tables against the available tables in the database.
    If all the tables defined in REQUIRED_TABLES are present in the
    database then this plugin is considered to be the correct plugin
    and the function will return back a generator that yields event
    objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cache: A SQLiteCache object.
      database: A database object (instance of SQLiteDatabase).

    Raises:
      errors.WrongPlugin: If the database does not contain all the tables
      defined in the REQUIRED_TABLES set.
      ValueError: If the database attribute is not passed in.
    """
    if database is None:
      raise ValueError(u'Database is not set.')

    if not frozenset(database.tables) >= self.REQUIRED_TABLES:
      raise errors.WrongPlugin(
          u'Not the correct database tables for: {0:s}'.format(self.NAME))

    # This will raise if unhandled keyword arguments are passed.
    super(SQLitePlugin, self).Process(parser_mediator)

    self.GetEntries(parser_mediator, cache=cache, database=database)
