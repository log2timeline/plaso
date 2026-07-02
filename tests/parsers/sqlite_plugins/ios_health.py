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
        # 4261 heart rate (sample) event data
        # 1 height (sample) event data
        # 18 resting heart rate (sample) event data
        # 6060 steps (sample) event data
        # 1109 weight (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8 + 4261 + 1 + 18 + 6060 + 1109)

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

        # TODO: remove after refactoring, determines the first index of a specific
        # event data type.
        indexes = {
            "ios:health:heart_rate": None,
            "ios:health:height": None,
            "ios:health:resting_heart_rate": None,
            "ios:health:steps": None,
            "ios:health:weight": None,
        }
        for index in range(0, number_of_event_data):
            event_data = storage_writer.GetAttributeContainerByIndex(
                "event_data", index
            )
            for key, value in indexes.items():
                if not value and event_data.data_type == key:
                    indexes[key] = index

        print(indexes)

        # Check heart rate (sample) event data.
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
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 11)
        self.CheckEventData(event_data, expected_event_values)

        # Check height (sample) event data.
        expected_event_values = {
            "data_type": "ios:health:height",
            "height": 1.7780000000000002,
            "start_time": "2020-04-03T18:23:55.320479+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8221)
        self.CheckEventData(event_data, expected_event_values)

        # Check resting heart rate (sample) event data.
        expected_event_values = {
            "added_time": "2020-03-23T10:41:56.913972+00:00",
            "data_type": "ios:health:resting_heart_rate",
            "end_time": "2020-03-23T02:13:34.627946+00:00",
            "hardware": "Watch4,3",
            "resting_heart_rate": 58,
            "source": "This Is’s Apple Watch",
            "start_time": "2020-03-22T11:37:44.656892+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 339)
        self.CheckEventData(event_data, expected_event_values)

        # Check steps (sample) event data.
        expected_event_values = {
            "data_type": "ios:health:steps",
            "device": "iPhone8,4",
            "duration": 9.09566879272461e-05,
            "end_time": "2020-03-21T22:22:55.703066+00:00",
            "number_of_steps": 2.0,
            "start_time": "2020-03-21T22:22:55.702975+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8)
        self.CheckEventData(event_data, expected_event_values)

        # Check weight (sample) event data.
        expected_event_values = {
            "data_type": "ios:health:weight",
            "start_time": "2020-04-03T18:23:55.320479+00:00",
            "weight": 81.64656,
            "weight_lbs": 179.99985302118716,
            "weight_stone": "12 Stone 12 Pounds",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8222)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
