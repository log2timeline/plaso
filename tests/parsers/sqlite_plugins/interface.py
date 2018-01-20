#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite plugin interface."""

from __future__ import unicode_literals

import sys
import unittest

from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import interface

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class TestSQLitePlugin(interface.SQLitePlugin):
  """Convenience class for a test SQLite plugin."""

  NAME = 'test'

  QUERIES = [(
      'SELECT Field1, Field2, Field3 FROM MyTable', 'ParseMyTableRow')]

  REQUIRED_TABLES = frozenset(['MyTable'])

  SCHEMAS = [
      {'MyTable': (
          'CREATE TABLE "MyTable" ( `Field1` TEXT, `Field2` INTEGER, '
          '`Field3` BLOB )')}]

  def __init__(self):
    """Initializes a SQLite plugin."""
    super(TestSQLitePlugin, self).__init__()
    self.results = []

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

    # If Python 2 is used field3 needs to be converted to a string
    # because it is a read-write buffer.
    if sys.version_info[0] < 3:
      field3 = str(field3)

    self.results.append((field1, field2, field3))

    event = time_events.TimestampEvent(
        timelib.Timestamp.NONE_TIMESTAMP,
        definitions.TIME_DESCRIPTION_NOT_A_TIME, data_type='fake')
    event.field1 = field1
    event.field2 = field2
    event.field3 = field3
    parser_mediator.ProduceEvent(event)


class SQLiteInterfaceTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite plugin interface."""

  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db-wal'])
  def testProcessWithWAL(self):
    """Tests the Process function on a database with WAL file."""
    plugin = TestSQLitePlugin()
    wal_file = self._GetTestFilePath(['wal_database.db-wal'])
    self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, wal_path=wal_file)

    expected_results = [
        ('Committed Text 1', 1, b'None'),
        ('Committed Text 2', 2, b'None'),
        ('Modified Committed Text 3', 4, b'None'),
        ('Committed Text 4', 5, b'None'),
        ('Committed Text 5', 7, b'None'),
        ('Committed Text 6', 8, b'None'),
        ('Committed Text 7', 9, b'None'),
        ('Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'),
        ('Unhashable Row 2', 11, b'More Binary Text!\x01\x02\x03'),
        ('New Text 1', 12, b'None'),
        ('New Text 2', 13, b'None')]

    self.assertEqual(expected_results, plugin.results)

  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db'])
  def testProcessWithoutWAL(self):
    """Tests the Process function on a database without WAL file."""
    plugin = TestSQLitePlugin()
    self._ParseDatabaseFileWithPlugin(['wal_database.db'], plugin)

    expected_results = [
        ('Committed Text 1', 1, b'None'),
        ('Committed Text 2', 2, b'None'),
        ('Deleted Text 1', 3, b'None'),
        ('Committed Text 3', 4, b'None'),
        ('Committed Text 4', 5, b'None'),
        ('Deleted Text 2', 6, b'None'),
        ('Committed Text 5', 7, b'None'),
        ('Committed Text 6', 8, b'None'),
        ('Committed Text 7', 9, b'None'),
        ('Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03')]

    self.assertEqual(plugin.results, expected_results)

  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db-wal'])
  def testCheckSchema(self):
    """Tests the CheckSchema function."""
    plugin = TestSQLitePlugin()

    # Test matching schema.
    _, database = self._OpenDatabaseFile(['wal_database.db'])

    schema_match = plugin.CheckSchema(database)
    self.assertTrue(schema_match)

    # Test schema change with WAL.
    wal_file = self._GetTestFilePath(['wal_database.db-wal'])
    _, database = self._OpenDatabaseFile(
        ['wal_database.db'], wal_path=wal_file)

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
