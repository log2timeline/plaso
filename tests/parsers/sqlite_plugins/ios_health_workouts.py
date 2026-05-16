#!/usr/bin/env python3
"""Tests for iOS Health Workouts SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_workouts
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWorkoutsPluginGoldenTest(test_lib.SQLitePluginTestCase):
    """Golden-value tests for the iOS Health Workouts SQLite database plugin."""

    def testProcess(self):
        """Tests the Process function on a healthdb_secure.sqlite file."""
        plugin = ios_health_workouts.IOSHealthWorkoutsPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )
        # 6 workouts (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check workouts (sample) event data.
        expected_event_values = {
            "activity_type": 37,
            "data_type": "ios:health:workouts",
            "duration": 1080.1204969882965,
            "duration_in_minutes": 18.002008283138274,
            "end_time": "2020-03-27T19:15:39.483301+00:00",
            "goal": None,
            "goal_type": 0,
            "start_time": "2020-03-27T18:57:39.362805+00:00",
            "total_basal_energy_burned": 26.335517881735733,
            "total_distance_km": 3.2479800059968365,
            "total_distance_miles": 2.0182005843062605,
            "total_energy_burned": 208.57206077784014,
            "total_flights_climbed": None,
            "total_w_steps": None,
            "workout_duration": "00:18:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
