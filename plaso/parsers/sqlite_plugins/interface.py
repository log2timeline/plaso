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

  def GetEntries(self, parser_context, cache=None, database=None, **kwargs):
    """Extracts event objects from a SQLite database.

    Args:
      parser_context: A parser context object (instance of ParserContext).
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
              parser_context, row, query=query, cache=cache, database=database)

          row = sql_results.fetchone()

      except sqlite3.DatabaseError as exception:
        logging.debug(u'SQLite error occured: {0:s}'.format(exception))

  def Process(self, parser_context, cache=None, database=None, **kwargs):
    """Determine if this is the right plugin for this database.

    This function takes a SQLiteDatabase object and compares the list
    of required tables against the available tables in the database.
    If all the tables defined in REQUIRED_TABLES are present in the
    database then this plugin is considered to be the correct plugin
    and the function will return back a generator that yields event
    objects.

    Args:
      parser_context: A parser context object (instance of ParserContext).
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
    super(SQLitePlugin, self).Process(parser_context, **kwargs)

    self.GetEntries(parser_context, cache=cache, database=database)
