#!/usr/bin/env python3
"""Tests for the Windows Search index (Windows.db) SQLite database plugin."""

import sqlite3
import unittest

from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import windows_search

from tests.parsers.sqlite_plugins import test_lib


class WindowsSearchPluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the Windows Search index (Windows.db) SQLite database plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plugin = windows_search.WindowsSearchPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["windows", "Windows.db"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 268)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # A folder, which has no size, owner or content type.
        expected_event_values = {
            "access_time": "2024-04-01T07:02:28.2253598+00:00",
            "creation_time": "2024-04-01T07:02:26.7877895+00:00",
            "data_type": "windows:search:db_item",
            "file_attributes": 8209,
            "gather_time": "2026-11-14T06:11:54.3943062+00:00",
            "is_folder": True,
            "item_type": "Directory",
            "modification_time": "2024-04-01T07:02:28.2253598+00:00",
            "path": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu",
            "work_identifier": 1,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # A text file.
        expected_event_values = {
            "access_time": "2026-11-14T06:11:12.8883541+00:00",
            "content_type": "text/plain",
            "creation_time": "2026-11-14T06:11:12.8850093+00:00",
            "data_type": "windows:search:db_item",
            "file_attributes": 32,
            "gather_time": "2026-11-14T06:12:12.0556313+00:00",
            "hostname": "WSUS01",
            "is_folder": False,
            "item_type": ".txt",
            "modification_time": "2026-11-14T06:11:12.8883541+00:00",
            "owner": "WSUS01\\Administrator",
            "path": "C:\\Users\\Administrator\\Documents\\Projects\\Alpha\\todo.txt",
            "size": 85,
            "summary": (
                "Alpha project todo: ship the beta, update the documentation, "
                "remove the old server.\r\n"
            ),
            "work_identifier": 162,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 161)
        self.CheckEventData(event_data, expected_event_values)

        # A text file that was modified after it was created.
        expected_event_values = {
            "access_time": "2026-11-14T06:11:32.9234783+00:00",
            "content_type": "text/plain",
            "creation_time": "2026-11-14T06:11:12.8635877+00:00",
            "data_type": "windows:search:db_item",
            "file_attributes": 32,
            "gather_time": "2026-11-14T06:12:12.1087188+00:00",
            "hostname": "WSUS01",
            "is_folder": False,
            "item_type": ".txt",
            "modification_time": "2026-11-14T06:11:32.9234783+00:00",
            "owner": "WSUS01\\Administrator",
            "path": "C:\\Users\\Administrator\\Documents\\quarterly-report.txt",
            "size": 150,
            "summary": (
                "Quarterly revenue report. Contains the codeword pineapple and the "
                "budget figures for Q3.\r\nAddendum: the figures were revised upward "
                "after the audit.\r\n"
            ),
            "work_identifier": 159,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 158)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithWriteAheadLog(self):
        """Tests the SQLite parser with a database that has a WAL file."""
        parser = sqlite.SQLiteParser()
        storage_writer = self._ParseFile(["windows", "Windows.db"], parser)

        # The SQLite parser parses the database and the database with the WAL
        # applied separately.
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 536)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseIndexItemRowWithUnsupportedValues(self):
        """Tests the ParseIndexItemRow function with unsupported values."""
        plugin = windows_search.WindowsSearchPlugin()
        query, _ = plugin.QUERIES[0]

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        with sqlite3.connect(":memory:") as database_connection:
            database_connection.row_factory = sqlite3.Row
            row = database_connection.execute(
                "SELECT 1 AS WorkId, X'0102' AS Size, NULL AS IsFolder, "
                "X'2000000000000000' AS FileAttributes, 1.5 AS DateCreated, "
                "NULL AS DateAccessed, NULL AS DateModified, NULL AS GatherTime, "
                "NULL AS ContentType, NULL AS ComputerName, NULL AS ItemType, "
                "NULL AS FileOwner, NULL AS ItemPathDisplay, NULL AS AutoSummary, "
                "NULL AS Title"
            ).fetchone()

        plugin.ParseIndexItemRow(parser_mediator, query, row)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(event_data.file_attributes, 32)
        self.assertIsNone(event_data.is_folder)
        self.assertIsNone(event_data.size)
        self.assertIsNone(event_data.creation_time)


if __name__ == "__main__":
    unittest.main()
