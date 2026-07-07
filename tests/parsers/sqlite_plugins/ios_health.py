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
        # 16 all watch sleep (sample) event data
        # 8 headphone audio level (sample) event data
        # 4261 heart rate (sample) event data
        # 1 height (sample) event data
        # 18 resting heart rate (sample) event data
        # 6060 steps (sample) event data
        # 8 source device event data
        # 1109 weight (sample) event data
        # 6 workouts (sample) event data
        # 266 wrist temperature (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        expected_number_of_event_data = (
            8 + 16 + 8 + 4261 + 1 + 18 + 6060 + 8 + 1109 + 6 + 266
        )
        self.assertEqual(number_of_event_data, expected_number_of_event_data)

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
            "synchronization_provenance": 1,
            "template_unique_name": "NewMoveGoalAchieved",
            "value_canonical_unit": "kcal",
            "value_in_canonical_unit": 480.0,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Check all watch sleep (sample) event data.
        expected_event_values = {
            "data_type": "ios:health:all_watch_sleep",
            "end_time": "2020-04-04T10:37:00.000000+00:00",
            "sleep_state_code": 0,
            "start_time": "2020-04-04T02:30:00.000000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 10394)
        self.CheckEventData(event_data, expected_event_values)

        # Check headphone audio level (sample) event data.
        expected_event_values = {
            "bundle_identifier": "com.apple.Music",
            "data_type": "ios:health:headphone_audio_levels",
            "decibels": 70.3830005252994,
            "device_local_identifier": "7C:04:D0:89:89:A0-tacl",
            "device_manufacturer": "Apple Inc.",
            "device_model": "0x2002",
            "device_name": "AirPods",
            "end_time": "2020-03-27T19:19:09.039616+00:00",
            "start_time": "2020-03-27T18:55:14.121677+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2672)
        self.CheckEventData(event_data, expected_event_values)

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
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8433)
        self.CheckEventData(event_data, expected_event_values)

        # Check resting heart rate (sample) event data.
        expected_event_values = {
            "added_time": "2020-03-23T10:41:56.913972+00:00",
            "data_type": "ios:health:resting_heart_rate",
            "end_time": "2020-03-23T02:13:34.627946+00:00",
            "hardware": "Watch4,3",
            "resting_heart_rate": 58,
            "source_name": "This Is’s Apple Watch",
            "start_time": "2020-03-22T11:37:44.656892+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 358)
        self.CheckEventData(event_data, expected_event_values)

        # Check source device event data.
        expected_event_values = {
            "added_time": "2020-03-21T22:33:20.752679+00:00",
            "data_type": "ios:health:source_devices",
            "device_name": "iPhone",
            "firmware": None,
            "hardware": "iPhone8,4",
            "local_identifier": None,
            "manufacturer": "Apple Inc.",
            "model": "iPhone",
            "software": "13.3.1",
            "synchronization_provenance": 0,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 11747)
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
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 8434)
        self.CheckEventData(event_data, expected_event_values)

        # Check workouts (sample) event data.
        expected_event_values = {
            "activity_type": 37,
            "data_type": "ios:health:workouts",
            "duration": 1080.1204969882965,
            "end_time": "2020-03-27T19:15:39.483301+00:00",
            "goal": None,
            "goal_type": 0,
            "start_time": "2020-03-27T18:57:39.362805+00:00",
            "total_basal_energy_burned": 26.335517881735733,
            "total_distance": 3.2479800059968365,
            "total_energy_burned": 208.57206077784014,
            "total_flights_climbed": None,
            "total_weekly_steps": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 11755)
        self.CheckEventData(event_data, expected_event_values)

        # Check wrist temperature (sample) event data.
        expected_event_values = {
            "added_time": "2020-03-22T01:00:56.379019+00:00",
            "algorithm_version": None,
            "data_type": "ios:health:wrist_temperature",
            "device_hardware": "Watch4,3",
            "device_manufacturer": "Apple Inc.",
            "device_model": "Watch",
            "device_name": "Apple Watch",
            "end_time": "2020-03-22T01:00:00.000000+00:00",
            "software_version": "6.1.3",
            "source_name": "This Is’s Apple Watch",
            "start_time": "2020-03-22T00:00:00.000000+00:00",
            "surface_temperature": None,
            "wrist_temperature": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 16)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
