#!/usr/bin/env python3
"""Tests for iOS Health Watch Worn Data SQLite plugin (golden values)."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_watch_worn_data
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWatchWornGoldenTest(test_lib.SQLitePluginTestCase):
    """Golden-value tests for the iOS Health Watch Worn Data SQLite plugin."""

    def testProcess(self):
        """Tests the Process function on a healthdb_secure.sqlite file."""
        plugin = ios_health_watch_worn_data.IOSHealthWatchWornPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )
        # 19 worn data (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 19)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check worn data (sample) event data.
        expected_event_values = {
            "data_type": "ios:health:watch_worn",
            "end_time": "2020-03-22T03:00:00.000000+00:00",
            "hours_off_before_next": 8,
            "hours_worn": 3,
            "start_time": "2020-03-22T00:00:00.000000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
