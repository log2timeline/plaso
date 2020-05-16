#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite database parser."""

import unittest

from plaso.parsers import sqlite
# Register all plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class SQLiteParserTest(test_lib.ParserTestCase):
  """Tests for the SQLite database parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = sqlite.SQLiteParser()
    parser.EnablePlugins(['chrome_27_history'])

    self.assertIsNotNone(parser)
    self.assertIsNone(parser._default_plugin)
    self.assertNotEqual(parser._plugins, [])
    self.assertEqual(len(parser._plugins), 1)

  def testFileParserChainMaintenance(self):
    """Tests that the parser chain is correctly maintained by the parser."""
    parser = sqlite.SQLiteParser()
    storage_writer = self._ParseFile(['contacts2.db'], parser)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(1, event_data.parser.count('/'))

  def testQueryDatabaseWithWAL(self):
    """Tests the Query function on a database with a WAL file."""
    database_file_path = self._GetTestFilePath(['wal_database.db'])
    self._SkipIfPathNotExists(database_file_path)

    database_wal_file_path = self._GetTestFilePath(['wal_database.db-wal'])
    self._SkipIfPathNotExists(database_wal_file_path)

    database = sqlite.SQLiteDatabase('wal_database.db')
    with open(database_file_path, 'rb') as database_file_object:
      with open(database_wal_file_path, 'rb') as wal_file_object:
        database.Open(database_file_object, wal_file_object=wal_file_object)

    row_results = []
    for row in database.Query('SELECT * FROM MyTable'):
      row_results.append((row['Field1'], row['Field2'], row['Field3']))

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

    self.assertEqual(expected_results, row_results)

  def testQueryDatabaseWithoutWAL(self):
    """Tests the Query function on a database without a WAL file."""
    database_file_path = self._GetTestFilePath(['wal_database.db'])
    self._SkipIfPathNotExists(database_file_path)

    database = sqlite.SQLiteDatabase('wal_database.db')
    with open(database_file_path, 'rb') as database_file_object:
      database.Open(database_file_object)

    row_results = []
    for row in database.Query('SELECT * FROM MyTable'):
      row_results.append((row['Field1'], row['Field2'], row['Field3']))

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

    self.assertEqual(expected_results, row_results)


if __name__ == '__main__':
  unittest.main()
