#!/usr/bin/env python3
"""Tests for iOS 16/17 Health Workouts (latest, workout_activities) plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_workouts_latest
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWorkoutsLatestTest(test_lib.SQLitePluginTestCase):
    """Tests for iOS Health Workouts latest SQLite database plugin (LOCAL)."""

    def testProcess(self):
        """Test the Process function."""
        plugin = ios_health_workouts_latest.IOSHealthWorkoutsLatestPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_17.sqlite"], plugin
        )
        # 29 workouts (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 29)

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
            "added_time": "2023-04-19T18:30:14.000000+00:00",
            "average_mets": None,
            "avg_heart_rate_bpm": None,
            "data_type": "ios:health:workouts_ios16",
            "end_time": "2023-04-15T15:00:29.000000+00:00",
            "goal": None,
            "goal_type": 0,
            "hardware": None,
            "humidity_percent": None,
            "latitude": None,
            "location_type": 3,
            "longitude": None,
            "max_ground_elevation_m": None,
            "max_heart_rate_bpm": None,
            "min_ground_elevation_m": None,
            "min_heart_rate_bpm": None,
            "software_version": "36",
            "source": "Connect",
            "start_time": "2023-04-15T14:34:28.000000+00:00",
            "temperature_c": None,
            "temperature_f": None,
            "timezone": "America/New_York",
            "total_active_energy_kcal": 439.0,
            "total_distance_km": 5.3,
            "total_distance_miles": 3.3,
            "total_resting_energy_kcal": None,
            "total_time_duration": "00:26:01",
            "workout_duration": "00:26:01",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
