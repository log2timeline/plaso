#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite plugin interface."""

from __future__ import unicode_literals

import sys
import unittest

from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import sqlite
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

  def ParseMyTableRow(self, parser_mediator, row, **unused_kwargs):
    """Parses a MyTable row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
    """
    file_entry = parser_mediator.GetFileEntry()
    path_spec = file_entry.path_spec
    location = path_spec.location
    from_wal = location.endswith('-wal')

    # If Python 2 is used pysqlite does not accept a Unicode string in
    # row['string'] and will raise "IndexError: Index must be int or string".
    row_keys = row.keys()

    column_index = row_keys.index('Field1')
    field1 = row[column_index]

    column_index = row_keys.index('Field2')
    field2 = row[column_index]

    column_index = row_keys.index('Field3')
    field3 = row[column_index]

    # If Python 2 is used field3 needs to be converted to a string
    # because it is a read-write buffer.
    if sys.version_info[0] < 3:
      field3 = str(field3)

    self.results.append(((field1, field2, field3), from_wal))

    event = time_events.TimestampEvent(
        timelib.Timestamp.NONE_TIMESTAMP,
        definitions.TIME_DESCRIPTION_NOT_A_TIME, data_type='fake')
    event.field1 = field1
    event.field2 = field2
    event.field3 = field3
    event.from_wal = location.endswith('-wal')
    parser_mediator.ProduceEvent(event)


class SQLiteInterfaceTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite plugin interface."""

  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db-wal'])
  def testProcessWithWAL(self):
    """Tests the Process function on a database with WAL file."""
    plugin = TestSQLitePlugin()
    cache = sqlite.SQLiteCache()
    wal_file = self._GetTestFilePath(['wal_database.db-wal'])
    self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, cache=cache, wal_path=wal_file)

    expected_results = [
        (('Committed Text 1', 1, b'None'), False),
        (('Committed Text 2', 2, b'None'), False),
        (('Deleted Text 1', 3, b'None'), False),
        (('Committed Text 3', 4, b'None'), False),
        (('Committed Text 4', 5, b'None'), False),
        (('Deleted Text 2', 6, b'None'), False),
        (('Committed Text 5', 7, b'None'), False),
        (('Committed Text 6', 8, b'None'), False),
        (('Committed Text 7', 9, b'None'), False),
        (('Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'), False),
        (('Modified Committed Text 3', 4, b'None'), True),
        (('Unhashable Row 2', 11, b'More Binary Text!\x01\x02\x03'), True),
        (('New Text 1', 12, b'None'), True),
        (('New Text 2', 13, b'None'), True)]

    self.assertEqual(expected_results, plugin.results)

  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db'])
  def testProcessWithoutWAL(self):
    """Tests the Process function on a database without WAL file."""
    plugin = TestSQLitePlugin()
    cache = sqlite.SQLiteCache()
    self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, cache=cache)

    expected_results = [
        (('Committed Text 1', 1, b'None'), False),
        (('Committed Text 2', 2, b'None'), False),
        (('Deleted Text 1', 3, b'None'), False),
        (('Committed Text 3', 4, b'None'), False),
        (('Committed Text 4', 5, b'None'), False),
        (('Deleted Text 2', 6, b'None'), False),
        (('Committed Text 5', 7, b'None'), False),
        (('Committed Text 6', 8, b'None'), False),
        (('Committed Text 7', 9, b'None'), False),
        (('Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'), False)]

    self.assertEqual(expected_results, plugin.results)

  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile(['wal_database.db-wal'])
  def testSchemaMatching(self):
    """Tests the Schema matching capabilities."""
    plugin = TestSQLitePlugin()
    cache = sqlite.SQLiteCache()

    # Test matching schema.
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, cache=cache)
    for event in storage_writer.GetEvents():
      self.assertTrue(event.schema_match)

    # Test schema change with WAL.
    wal_file = self._GetTestFilePath(['wal_database.db-wal'])
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, cache=cache, wal_path=wal_file)

    for event in storage_writer.GetEvents():
      if event.from_wal:
        self.assertFalse(event.schema_match)
      else:
        self.assertTrue(event.schema_match)

    # Add schema change from WAL file and test again.
    plugin.SCHEMAS.append(
        {'MyTable':
         'CREATE TABLE "MyTable" ( `Field1` TEXT, `Field2` INTEGER, `Field3` '
         'BLOB , NewField TEXT)',
         'NewTable':
         'CREATE TABLE NewTable(NewTableField1 TEXT, NewTableField2 TEXT)'})

    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, cache=cache, wal_path=wal_file)
    for event in storage_writer.GetEvents():
      self.assertTrue(event.schema_match)

    # Test without original schema.
    del plugin.SCHEMAS[0]
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['wal_database.db'], plugin, cache=cache, wal_path=wal_file)

    for event in storage_writer.GetEvents():
      if event.from_wal:
        self.assertTrue(event.schema_match)
      else:
        self.assertFalse(event.schema_match)


if __name__ == '__main__':
  unittest.main()
