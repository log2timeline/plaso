#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite plugin interface."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import interface

from tests.parsers.sqlite_plugins import test_lib


class TestEventData(events.EventData):
  """Event data for testing the SQLite plugin interface.

  Attributes:
    field1 (str): first field.
    field2 (str): second field.
    field3 (str): third field.
    from_wal (bool): True if the event data was created from a SQLite database
        with a WAL file.
  """

  DATA_TYPE = 'test:sqlite_plugins:interface'

  def __init__(self):
    """Initializes event data."""
    super(TestEventData, self).__init__(data_type=self.DATA_TYPE)
    self.field1 = None
    self.field2 = None
    self.field3 = None
    self.from_wal = None


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

    file_entry = parser_mediator.GetFileEntry()

    field1 = self._GetRowValue(query_hash, row, 'Field1')
    field2 = self._GetRowValue(query_hash, row, 'Field2')
    field3 = self._GetRowValue(query_hash, row, 'Field3')

    # If Python 2 is used field3 needs to be converted to a string
    # because it is a read-write buffer.
    if py2to3.PY_2 and field3 is not None:
      field3 = str(field3)

    self.results.append((field1, field2, field3))

    event_data = TestEventData()
    event_data.field1 = field1
    event_data.field2 = field2
    event_data.field3 = field3
    event_data.from_wal = file_entry.path_spec.location.endswith('-wal')

    event = time_events.TimestampEvent(
        timelib.Timestamp.NONE_TIMESTAMP,
        definitions.TIME_DESCRIPTION_NOT_A_TIME)

    parser_mediator.ProduceEventWithEventData(event, event_data)


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
