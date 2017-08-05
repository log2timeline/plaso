#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite plugin interface."""

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

  NAME = u'test'

  QUERIES = [(
      u'SELECT Field1, Field2, Field3 FROM MyTable', u'ParseMyTableRow')]

  REQUIRED_TABLES = frozenset([u'MyTable'])

  SCHEMAS = [
      {u'MyTable':
       u'CREATE TABLE "MyTable" ( `Field1` TEXT, `Field2` INTEGER, '
       u'`Field3` BLOB )'}]

  def __init__(self):
    """Initializes SQLite plugin."""
    super(TestSQLitePlugin, self).__init__()
    self.results = []

  def ParseMyTableRow(self, parser_mediator, row, **unused_kwargs):
    """Parses a MyTable row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
    """
    file_entry = parser_mediator.GetFileEntry()
    path_spec = file_entry.path_spec
    location = path_spec.location
    from_wal = location.endswith(u'-wal')
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    # Also, Field3 needs to be converted to a string if Python 2 is used
    # because it is a read-write buffer.
    field3 = row['Field3']
    if sys.version_info[0] < 3:
      field3 = str(field3)
    self.results.append(((row['Field1'], row['Field2'], field3), from_wal))

    event = time_events.TimestampEvent(
        timelib.Timestamp.NONE_TIMESTAMP,
        definitions.TIME_DESCRIPTION_NOT_A_TIME, data_type=u'fake')
    event.field1 = row['Field1']
    event.field2 = row['Field2']
    event.field3 = field3
    event.from_wal = location.endswith(u'-wal')
    parser_mediator.ProduceEvent(event)


class SQLiteInterfaceTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite plugin interface."""

  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db-wal'])
  def testProcessWithWAL(self):
    """Tests the Process function on a database with WAL file."""
    plugin = TestSQLitePlugin()
    cache = sqlite.SQLiteCache()
    wal_file = self._GetTestFilePath([u'wal_database.db-wal'])
    self._ParseDatabaseFileWithPlugin(
        [u'wal_database.db'], plugin, cache=cache, wal_path=wal_file)

    expected_results = [
        ((u'Committed Text 1', 1, b'None'), False),
        ((u'Committed Text 2', 2, b'None'), False),
        ((u'Deleted Text 1', 3, b'None'), False),
        ((u'Committed Text 3', 4, b'None'), False),
        ((u'Committed Text 4', 5, b'None'), False),
        ((u'Deleted Text 2', 6, b'None'), False),
        ((u'Committed Text 5', 7, b'None'), False),
        ((u'Committed Text 6', 8, b'None'), False),
        ((u'Committed Text 7', 9, b'None'), False),
        ((u'Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'), False),
        ((u'Modified Committed Text 3', 4, b'None'), True),
        ((u'Unhashable Row 2', 11, b'More Binary Text!\x01\x02\x03'), True),
        ((u'New Text 1', 12, b'None'), True),
        ((u'New Text 2', 13, b'None'), True)]

    self.assertEqual(expected_results, plugin.results)

  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db'])
  def testProcessWithoutWAL(self):
    """Tests the Process function on a database without WAL file."""
    plugin = TestSQLitePlugin()
    cache = sqlite.SQLiteCache()
    self._ParseDatabaseFileWithPlugin(
        [u'wal_database.db'], plugin, cache=cache)

    expected_results = [
        ((u'Committed Text 1', 1, b'None'), False),
        ((u'Committed Text 2', 2, b'None'), False),
        ((u'Deleted Text 1', 3, b'None'), False),
        ((u'Committed Text 3', 4, b'None'), False),
        ((u'Committed Text 4', 5, b'None'), False),
        ((u'Deleted Text 2', 6, b'None'), False),
        ((u'Committed Text 5', 7, b'None'), False),
        ((u'Committed Text 6', 8, b'None'), False),
        ((u'Committed Text 7', 9, b'None'), False),
        ((u'Unhashable Row 1', 10, b'Binary Text!\x01\x02\x03'), False)]

    self.assertEqual(expected_results, plugin.results)

  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db'])
  @shared_test_lib.skipUnlessHasTestFile([u'wal_database.db-wal'])
  def testSchemaMatching(self):
    """Tests the Schema matching capabilities."""
    plugin = TestSQLitePlugin()
    cache = sqlite.SQLiteCache()

    # Test matching schema.
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'wal_database.db'], plugin, cache=cache)
    for event in storage_writer.GetEvents():
      self.assertTrue(event.schema_match)

    # Test schema change with WAL.
    wal_file = self._GetTestFilePath([u'wal_database.db-wal'])
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'wal_database.db'], plugin, cache=cache, wal_path=wal_file)

    for event in storage_writer.GetEvents():
      if event.from_wal:
        self.assertFalse(event.schema_match)
      else:
        self.assertTrue(event.schema_match)

    # Add schema change from WAL file and test again.
    plugin.SCHEMAS.append(
        {u'MyTable':
         u'CREATE TABLE "MyTable" ( `Field1` TEXT, `Field2` INTEGER, `Field3` '
         u'BLOB , NewField TEXT)',
         u'NewTable':
         u'CREATE TABLE NewTable(NewTableField1 TEXT, NewTableField2 TEXT)'})

    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'wal_database.db'], plugin, cache=cache, wal_path=wal_file)
    for event in storage_writer.GetEvents():
      self.assertTrue(event.schema_match)

    # Test without original schema.
    del plugin.SCHEMAS[0]
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'wal_database.db'], plugin, cache=cache, wal_path=wal_file)

    for event in storage_writer.GetEvents():
      if event.from_wal:
        self.assertTrue(event.schema_match)
      else:
        self.assertFalse(event.schema_match)


if __name__ == '__main__':
  unittest.main()
