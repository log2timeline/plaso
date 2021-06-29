#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite plugin interface."""

import unittest

from plaso.parsers.sqlite_plugins import interface

from tests.parsers.sqlite_plugins import test_lib


class TestSQLitePlugin(interface.SQLitePlugin):
  """SQLite plugin for testing purposes."""

  NAME = 'test'

  QUERIES = [(
      'SELECT Field1, Field2, Field3 FROM MyTable', 'ParseMyTableRow')]

  REQUIRED_STRUCTURE = {
      'MyTable': frozenset(['Field1'])}

  SCHEMAS = [
      {'MyTable': (
          'CREATE TABLE "MyTable" ( `Field1` TEXT, `Field2` INTEGER, '
          '`Field3` BLOB )')}]

  def __init__(self):
    """Initializes a SQLite plugin."""
    super(TestSQLitePlugin, self).__init__()
    self.results = []

  # pylint: disable=unused-argument
  def ParseMyTableRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a MyTable row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    field1 = self._GetRowValue(query_hash, row, 'Field1')
    field2 = self._GetRowValue(query_hash, row, 'Field2')
    field3 = self._GetRowValue(query_hash, row, 'Field3')

    self.results.append((field1, field2, field3))


class SQLiteInterfaceTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite plugin interface."""

  def testProcessWithWAL(self):
    """Tests the Process function on a database with WAL file."""
    plugin = TestSQLitePlugin()
    self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, wal_path_segments=['wal_database.db-wal'])

    expected_results = [
        ('Committed Text 1', 1, None),
        ('Committed Text 2', 2, None),
        ('Modified Committed Text 3', 4, None),
        ('Committed Text 4', 5, None),
        ('Committed Text 5', 7, None),
        ('Committed Text 6', 8, None),
        ('Committed Text 7', 9, None),
        ('Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'),
        ('Unhashable Row 2', 11, b'More Binary Text!\x01\x02\x03'),
        ('New Text 1', 12, None),
        ('New Text 2', 13, None)]

    self.assertEqual(plugin.results, expected_results)

  def testProcessWithoutWAL(self):
    """Tests the Process function on a database without WAL file."""
    plugin = TestSQLitePlugin()
    self._ParseDatabaseFileWithPlugin(['wal_database.db'], plugin)

    expected_results = [
        ('Committed Text 1', 1, None),
        ('Committed Text 2', 2, None),
        ('Deleted Text 1', 3, None),
        ('Committed Text 3', 4, None),
        ('Committed Text 4', 5, None),
        ('Deleted Text 2', 6, None),
        ('Committed Text 5', 7, None),
        ('Committed Text 6', 8, None),
        ('Committed Text 7', 9, None),
        ('Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03')]

    self.assertEqual(plugin.results, expected_results)

  def testCheckSchema(self):
    """Tests the CheckSchema function."""
    plugin = TestSQLitePlugin()

    # Test matching schema.
    _, database = self._OpenDatabaseFile(['wal_database.db'])

    schema_match = plugin.CheckSchema(database)
    self.assertTrue(schema_match)

    # Test schema change with WAL.
    _, database = self._OpenDatabaseFile(
        ['wal_database.db'], wal_path_segments=['wal_database.db-wal'])

    schema_match = plugin.CheckSchema(database)
    self.assertFalse(schema_match)

    # Add schema change from WAL file and test again.
    plugin.SCHEMAS.append(
        {'MyTable':
         'CREATE TABLE "MyTable" ( `Field1` TEXT, `Field2` INTEGER, `Field3` '
         'BLOB , NewField TEXT)',
         'NewTable':
         'CREATE TABLE NewTable(NewTableField1 TEXT, NewTableField2 TEXT)'})

    schema_match = plugin.CheckSchema(database)
    self.assertTrue(schema_match)

    # Test without original schema.
    del plugin.SCHEMAS[0]

    schema_match = plugin.CheckSchema(database)
    self.assertTrue(schema_match)


if __name__ == '__main__':
  unittest.main()
