#!/usr/bin/env python3
"""Tests for iOS Health - All Watch Sleep (iOS 17+) SQLite plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_all_watch_sleep_latest

from tests.parsers.sqlite_plugins import test_lib


class IOSHealthAllWatchSleepLatestPluginGoldenTest(test_lib.SQLitePluginTestCase):
    """Golden-value tests for the iOS Health - All Watch Sleep (stages) plugin."""

    def testProcess(self):
        """Tests the Process function on a healthdb_secure.sqlite file."""
        plugin = ios_health_all_watch_sleep_latest.IOSHealthAllWatchSleepLatestPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_17.sqlite"], plugin
        )
        # 93 watch sleep (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 93)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check watch sleep event data.
        expected_event_values = {
            "data_type": "ios:health:all_watch_sleep_ios17",
            "end_time": "2024-07-23T03:44:36.786187+00:00",
            "sleep_state_code": 3,
            "sleep_state_hms": "00:19:00",
            "start_time": "2024-07-23T03:25:36.786187+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
