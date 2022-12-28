#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite database parser."""

import unittest

from plaso.parsers import sqlite
# Register all plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class SQLiteDatabaseTest(test_lib.ParserTestCase):
  """Tests for the SQLite database."""

  # TODO: add tests for tables property
  # TODO: add tests for _CopyFileObjectToTemporaryFile
  # TODO: add tests for Open and Close

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    database_file_path = self._GetTestFilePath(['contacts2.db'])
    self._SkipIfPathNotExists(database_file_path)

    database = sqlite.SQLiteDatabase('contacts2.db')
    with open(database_file_path, 'rb') as database_file_object:
      database.Open(database_file_object)
      database.Close()

  def testOpenCloseOnDatabaseWithDotInTableName(self):
    """Tests Open and Close on a database with a dot in a table name."""
    database_file_path = self._GetTestFilePath(['data.db'])
    self._SkipIfPathNotExists(database_file_path)

    database = sqlite.SQLiteDatabase('data.db')
    with open(database_file_path, 'rb') as database_file_object:
      database.Open(database_file_object)
      database.Close()

  def testQueryOnDatabaseWithWAL(self):
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

  def testQueryOnDatabaseWithoutWAL(self):
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


class SQLiteParserTest(test_lib.ParserTestCase):
  """Tests for the SQLite database parser."""

  # pylint: disable=protected-access

  # TODO: add tests for _OpenDatabaseWithWAL

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = sqlite.SQLiteParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

    parser.EnablePlugins(['chrome_27_history'])
    self.assertEqual(len(parser._plugins_per_name), 1)

  def testGetFormatSpecification(self):
    """Tests the GetFormatSpecification function."""
    format_specification = sqlite.SQLiteParser.GetFormatSpecification()
    self.assertIsNotNone(format_specification)

  def testParseFileEntry(self):
    """Tests the ParseFileEntry function."""
    parser = sqlite.SQLiteParser()
    storage_writer = self._ParseFile(['contacts2.db'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseFileEntryOnDatabaseWithDotInTableName(self):
    """Tests ParseFileEntry on a database with a dot in a table name."""
    parser = sqlite.SQLiteParser()
    storage_writer = self._ParseFile(['data.db'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
