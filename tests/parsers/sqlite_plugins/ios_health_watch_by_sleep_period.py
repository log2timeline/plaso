#!/usr/bin/env python3
"""Tests for the iOS Health - Watch by Sleep Period InBed plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_watch_by_sleep_period
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWatchBySleepPeriodPluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the iOS Health - Watch by Sleep Period InBed plugin."""

    def testProcess(self):
        """Test overall plugin handling including parsing a real SQLite file."""
        plugin = ios_health_watch_by_sleep_period.IOSHealthWatchBySleepPeriodPlugin()

        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_15.sqlite"], plugin
        )
        # 3 watch by sleep period (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        expected_event_values = {
            "asleep_percent": 100.0,
            "data_type": "ios:health:watch_by_sleep_period",
            "end_time": "2021-01-17T11:13:30.990108+00:00",
            "in_bed_duration": 0.0,
            "in_bed_percent": 0.0,
            "start_time": "2020-12-31T03:56:28.330994+00:00",
            "total_duration": 7493.0,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
