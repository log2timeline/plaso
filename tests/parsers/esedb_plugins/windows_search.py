#!/usr/bin/env python3
"""Tests for the Windows Search ESE database plugin."""

import unittest

from plaso.parsers import esedb
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers.esedb_plugins import windows_search

from tests.parsers.esedb_plugins import test_lib


class WindowsSearchESEDBPluginTest(test_lib.ESEDBPluginTestCase):
    """Tests for the Windows Search ESE database plugin."""

    def _CheckRequiredTables(self, path_segments):
        """Checks if an ESE database file has the tables required by the plugin.

        Args:
          path_segments (list[str]): path segments inside the test data directory.

        Returns:
          bool: True if the database has the tables required by the plugin.
        """
        plugin = windows_search.WindowsSearchESEDBPlugin()

        file_entry = self._GetTestFileEntry(path_segments)
        file_object = file_entry.GetFileObject()

        database = esedb.ESEDatabase()
        database.Open(file_object)

        try:
            return plugin.CheckRequiredTables(database)
        finally:
            database.Close()

    def testCheckRequiredTables(self):
        """Tests the CheckRequiredTables function."""
        result = self._CheckRequiredTables(["Windows.edb"])
        self.assertTrue(result)

        # Other ESE database files must not be parsed as a Windows Search
        # database.
        result = self._CheckRequiredTables(["Catalog1.edb"])
        self.assertFalse(result)

        result = self._CheckRequiredTables(["SRUDB.dat"])
        self.assertFalse(result)

        result = self._CheckRequiredTables(["WebCacheV01.dat"])
        self.assertFalse(result)

    def testParseSystemIndexTable(self):
        """Tests the ParseSystemIndexTable function."""
        plugin = windows_search.WindowsSearchESEDBPlugin()

        parser_mediator = parsers_mediator.ParserMediator()

        with self.assertRaises(ValueError):
            plugin.ParseSystemIndexTable(parser_mediator, table=None)

        storage_writer = self._CreateStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        file_entry = self._GetTestFileEntry(["Windows.edb"])
        parser_mediator.SetFileEntry(file_entry)
        parser_mediator.AppendToParserChain("esedb")
        parser_mediator.SignalAbort()

        file_object = file_entry.GetFileObject()

        database = esedb.ESEDatabase()
        database.Open(file_object)

        try:
            table = database.GetTableByName("SystemIndex_0A")
            plugin.ParseSystemIndexTable(parser_mediator, table=table)

        finally:
            database.Close()

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

    def testProcess(self):
        """Tests the Process function."""
        plugin = windows_search.WindowsSearchESEDBPlugin()
        storage_writer = self._ParseESEDBFileWithPlugin(["Windows.edb"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 322)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A directory, where the size is not set.
        expected_event_values = {
            "data_type": "windows:search:item",
            "file_size": None,
            "item_path": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu",
            "item_url": "file:C:/ProgramData/Microsoft/Windows/Start Menu",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A file.
        expected_event_values = {
            "access_time": "2015-08-25T10:58:41.3638868+00:00",
            "hostname": "STUDENT-PC1",
            "creation_time": "2015-08-25T10:58:40.6763868+00:00",
            "data_type": "windows:search:item",
            "document_identifier": 229,
            "file_attribute_flags": 0x00000020,
            "file_owner": "INTERNAL\\bperry",
            "file_size": 12530,
            "gather_time": "2015-08-25T10:59:23.9888868+00:00",
            "item_path": (
                "C:\\Users\\bperry\\My Documents\\Poultry Studies\\"
                "Introduction to Chicken.docx"
            ),
            "item_url": (
                "file:C:/Users/bperry/Documents/Poultry Studies/"
                "Introduction to Chicken.docx"
            ),
            "modification_time": "2015-08-25T10:58:41.7076368+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 225)
        self.CheckEventData(event_data, expected_event_values)

        # An Internet Explorer history item, where the file attribute flags are
        # not set.
        expected_event_values = {
            "access_time": None,
            "creation_time": None,
            "data_type": "windows:search:item",
            "document_identifier": 264,
            "file_attribute_flags": None,
            "gather_time": "2015-09-16T19:10:54.8041895+00:00",
            "item_path": "http://www.honda.com/",
            "item_url": (
                "iehistory://{S-1-5-21-226059406-2984137831-1201299043-1107}/"
                "http://www.honda.com"
            ),
            "modification_time": "2015-09-16T19:10:48.1557520+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 250)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
