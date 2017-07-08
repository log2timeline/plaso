#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite database parser."""

import sys
import unittest

from plaso.parsers import sqlite
# Register all plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SQLiteParserTest(test_lib.ParserTestCase):
  """Tests for the SQLite database parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = sqlite.SQLiteParser()
    parser.EnablePlugins([u'chrome_history'])

    self.assertIsNotNone(parser)
    self.assertIsNone(parser._default_plugin)
    self.assertNotEqual(parser._plugins, [])
    self.assertEqual(len(parser._plugins), 1)

  @shared_test_lib.skipUnlessHasTestFile([u'contacts2.db'])
  def testFileParserChainMaintenance(self):
    """Tests that the parser chain is correctly maintained by the parser."""
    parser = sqlite.SQLiteParser()
    storage_writer = self._ParseFile([u'contacts2.db'], parser)

    for event in storage_writer.GetEvents():
      chain = event.parser
      self.assertEqual(1, chain.count(u'/'))

  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db-wal'])
  def testQueryDatabaseWithWAL(self):
    """Tests the Query function on a database with a WAL file."""
    database_file = self._GetTestFilePath([u'wal_database.db'])
    wal_file = self._GetTestFilePath([u'wal_database.db-wal'])

    database = sqlite.SQLiteDatabase(u'wal_database.db')
    with open(database_file, 'rb') as database_file_object:
      with open(wal_file, 'rb') as wal_file_object:
        database.Open(database_file_object, wal_file_object=wal_file_object)

    row_results = []
    for row in database.Query(u'SELECT * FROM MyTable'):
      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      # Also, Field3 needs to be converted to a string if Python 2 is used
      # because it is a read-write buffer.
      field3 = row['Field3']
      if sys.version_info[0] < 3:
        field3 = str(field3)
      row_results.append((
          row['Field1'], row['Field2'], field3))

    expected_results = [
        (u'Committed Text 1', 1, b'None'),
        (u'Committed Text 2', 2, b'None'),
        (u'Modified Committed Text 3', 4, b'None'),
        (u'Committed Text 4', 5, b'None'),
        (u'Committed Text 5', 7, b'None'),
        (u'Committed Text 6', 8, b'None'),
        (u'Committed Text 7', 9, b'None'),
        (u'Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'),
        (u'Unhashable Row 2', 11, b'More Binary Text!\x01\x02\x03'),
        (u'New Text 1', 12, b'None'),
        (u'New Text 2', 13, b'None')]

    self.assertEqual(expected_results, row_results)

  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db'])
  def testQueryDatabaseWithoutWAL(self):
    """Tests the Query function on a database without a WAL file."""
    database_file = self._GetTestFilePath([u'wal_database.db'])

    database = sqlite.SQLiteDatabase(u'wal_database.db')
    with open(database_file, u'rb') as database_file_object:
      database.Open(database_file_object)

    row_results = []
    for row in database.Query(u'SELECT * FROM MyTable'):
      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      # Also, Field3 needs to be converted to a string if Python 2 is used
      # because it is a read-write buffer.
      field3 = row['Field3']
      if sys.version_info[0] < 3:
        field3 = str(field3)
      row_results.append((
          row['Field1'], row['Field2'], field3))

    expected_results = [
        (u'Committed Text 1', 1, b'None'),
        (u'Committed Text 2', 2, b'None'),
        (u'Deleted Text 1', 3, b'None'),
        (u'Committed Text 3', 4, b'None'),
        (u'Committed Text 4', 5, b'None'),
        (u'Deleted Text 2', 6, b'None'),
        (u'Committed Text 5', 7, b'None'),
        (u'Committed Text 6', 8, b'None'),
        (u'Committed Text 7', 9, b'None'),
        (u'Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03')]

    self.assertEqual(expected_results, row_results)


if __name__ == '__main__':
  unittest.main()
