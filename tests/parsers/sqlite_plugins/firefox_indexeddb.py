#!/usr/bin/env python3
"""Tests for the Mozilla Firefox IndexedDB database plugin."""

import sqlite3
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import firefox_indexeddb

from tests.parsers.sqlite_plugins import test_lib


@unittest.skipIf(
    firefox_indexeddb.dfindexeddb_gecko is None, "missing dfindexeddb support"
)
class FirefoxIndexedDBPluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the Mozilla Firefox IndexedDB database plugin."""

    def testCheckRequiredTablesAndColumns(self):
        """Tests the CheckRequiredTablesAndColumns function."""
        plugin = firefox_indexeddb.FirefoxIndexedDBPlugin()

        _, database = self._OpenDatabaseFile(["firefox", "indexeddb.sqlite"])
        try:
            result = plugin.CheckRequiredTablesAndColumns(database)
            self.assertTrue(result)

            result = plugin.CheckSchema(database)
            self.assertTrue(result)
        finally:
            database.Close()

        for path_segments in (
            ["chrome", "History"],
            ["firefox", "firefox_10_cookies.sqlite"],
            ["firefox", "places.sqlite"],
            ["safari", "History.db"],
        ):
            _, database = self._OpenDatabaseFile(path_segments)
            try:
                result = plugin.CheckRequiredTablesAndColumns(database)
                self.assertFalse(result)
            finally:
                database.Close()

    def testParseRecordRowWithInvalidValue(self):
        """Tests the ParseRecordRow function with a value that cannot be decoded."""
        plugin = firefox_indexeddb.FirefoxIndexedDBPlugin()

        storage_writer = self._CreateStorageWriter()

        parser_mediator = parsers_mediator.ParserMediator()
        parser_mediator.SetStorageWriter(storage_writer)

        query = (
            "SELECT 'testdb' AS database_name, 'http://127.0.0.1' AS origin, "
            "'notes' AS object_store_name, X'306c33' AS key, X'00' AS data"
        )

        database = sqlite3.connect(":memory:")
        try:
            database.row_factory = sqlite3.Row
            row = database.execute(query).fetchone()

            plugin.ParseRecordRow(parser_mediator, query, row)
        finally:
            database.close()

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "data_type": "firefox:indexeddb:record",
            "database_name": "testdb",
            "javascript_dates": None,
            "key": '"k2"',
            "object_store_name": "notes",
            "origin": "http://127.0.0.1",
            "value": None,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testPluginRegistration(self):
        """Tests that the plugin is registered with the SQLite parser."""
        plugin_names = sqlite.SQLiteParser.GetPluginNames()
        self.assertIn("firefox_indexeddb", plugin_names)

    def testProcess(self):
        """Tests the Process function on a Firefox IndexedDB database."""
        plugin = firefox_indexeddb.FirefoxIndexedDBPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["firefox", "indexeddb.sqlite"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "firefox:indexeddb:record",
            "database_name": "testdb",
            "javascript_dates": ["2026-11-26T10:00:00.000000+00:00"],
            "key": "1",
            "object_store_name": "notes",
            "origin": "http://127.0.0.1:34591",
            "value": (
                '{"id": 1, "title": "hello", "created": 2026-11-26T10:00:00.000Z}'
            ),
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "firefox:indexeddb:record",
            "database_name": "testdb",
            "javascript_dates": None,
            "key": '"k2"',
            "object_store_name": "notes",
            "origin": "http://127.0.0.1:34591",
            "value": (
                '{"id": "k2", "title": "world", "blob": Blob(index: 0, size: 3, '
                'type: "text/plain")}'
            ),
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
