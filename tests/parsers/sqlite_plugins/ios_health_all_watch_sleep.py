#!/usr/bin/env python3
"""Tests for iOS Health - All Watch Sleep (iOS 13-16) SQLite plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_all_watch_sleep
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthAllWatchSleepPluginGoldenTest(test_lib.SQLitePluginTestCase):
    """Golden-value tests for the iOS Health - All Watch Sleep (0/1) plugin."""

    def testProcess(self):
        """Tests the Process function on a healthdb_secure.sqlite file."""
        plugin = ios_health_all_watch_sleep.IOSHealthAllWatchSleepPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )
        # 16 watch sleep (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 16)

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
            "data_type": "ios:health:all_watch_sleep",
            "end_time": "2020-04-04T09:40:00.000000+00:00",
            "sleep_state_code": 1,
            "sleep_state_hms": "07:10:00",
            "start_time": "2020-04-04T02:30:00.000000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
