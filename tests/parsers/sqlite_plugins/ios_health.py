#!/usr/bin/env python3
"""Tests for iOS Health (healthdb_secure.sqlite) SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health

from tests.parsers.sqlite_plugins import test_lib


class IOSHealthTest(test_lib.SQLitePluginTestCase):
    """Tests for iOS Health (healthdb_secure.sqlite) SQLite database plugin."""

    def testProcess(self):
        """Test the Process function."""
        plugin = ios_health.IOSHealthPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )

        # 8 achievement event data
        # 4261 heart rate event data
        # 1 height event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8 + 4261 + 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check achievement event data.
        expected_event_values = {
            "creation_time": "2020-03-23T21:53:00.233904+00:00",
            "creator_device": 1,
            "data_type": "ios:health:achievement",
            "earned_date": "2020-03-23",
            "sync_provenance": 1,
            "template_unique_name": "NewMoveGoalAchieved",
            "value_canonical_unit": "kcal",
            "value_in_canonical_unit": 480.0,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Check heart rate event data.
        expected_event_values = {
            "added_time": "2020-03-22T00:54:14.754652+00:00",
            "bpm": 73,
            "context": 1.0,
            "data_type": "ios:health:heart_rate",
            "device_name": "Apple Watch",
            "end_time": "2020-03-22T00:52:59.032980+00:00",
            "hardware": "Watch4,3",
            "manufacturer": "Apple Inc.",
            "software_version": "6.1.3",
            "source_name": "This Is’s Apple Watch",
            "start_time": "2020-03-22T00:52:59.032980+00:00",
            "time_zone": "America/New_York",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8)
        self.CheckEventData(event_data, expected_event_values)

        # Check height event data.
        expected_event_values = {
            "data_type": "ios:health:height",
            "date_time": "2020-04-03T18:23:55.320479+00:00",
            "height": 1.7780000000000002,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8 + 4261)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
