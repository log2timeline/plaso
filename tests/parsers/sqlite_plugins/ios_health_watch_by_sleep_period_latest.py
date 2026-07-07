#!/usr/bin/env python3
"""Tests for the iOS Health Watch by Sleep Period Latest (iOS 17+) plugin."""

import unittest

from plaso.parsers.sqlite_plugins import (
    ios_health_watch_by_sleep_period_latest as ios_health_watch_by_sleep,
)

from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWatchBySleepPeriodLatestPluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the iOS Health Watch by Sleep Period Latest plugin."""

    def testProcess(self):
        """Test overall plugin handling including parsing a real SQLite file."""
        plugin = ios_health_watch_by_sleep.IOSHealthWatchBySleepPeriodLatestPlugin()

        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_17.sqlite"], plugin
        )
        # 4 watch by sleep period (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        expected_event_values = {
            "awake_duration_hms": "00:01:00",
            "awake_percent": 0.24,
            "core_duration_hms": "03:34:00",
            "core_percent": 52.2,
            "data_type": "ios:health:watch_by_sleep_period_latest",
            "deep_duration_hms": "01:28:30",
            "deep_percent": 21.59,
            "end_date_str": "2024-07-23 10:15:36.786187",
            "rem_duration_hms": "01:46:30",
            "rem_percent": 25.98,
            "start_date_str": "2024-07-23 03:25:36.786187",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
