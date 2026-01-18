#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        ['healthdb_secure.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    self.assertEqual(
        storage_writer.GetNumberOfAttributeContainers('extraction_warning'), 0)
    self.assertEqual(
        storage_writer.GetNumberOfAttributeContainers('recovery_warning'), 0)

    expected_event_values = {
        'activity_type': 37,
        'added_timestamp_str': '2020-03-27T19:15:40+00:00',
        'average_mets': 11.6,
        'avg_heart_rate_bpm': 185,
        'data_type': 'ios:health:workouts_latest',
        'date_time': '2020-03-27T18:57:39+00:00',
        'end_date_str': '2020-03-27T19:15:39+00:00',
        'goal': None,
        'goal_type': 0,
        'hardware': 'Apple Watch Series 4 Cellular - 40mm',
        'humidity_percent': 61,
        'latitude': 35.65931351393057,
        'location_type': 2,
        'longitude': -78.87268893428042,
        'max_ground_elevation_m': 106.8,
        'max_heart_rate_bpm': 195,
        'min_ground_elevation_m': 96.41,
        'min_heart_rate_bpm': 174,
        'software_version': 'watchOS 6.1.3',
        'source': "This Is’s Apple Watch",
        'start_date_str': '2020-03-27T18:57:39+00:00',
        'temperature_c': 24.44,
        'temperature_f': 76.0,
        'timezone': 'America/New_York',
        'total_active_energy_kcal': 208.57,
        'total_distance_km': 3.25,
        'total_distance_miles': 2.02,
        'total_resting_energy_kcal': 26.34,
        'total_time_duration': '00:18:00',
        'workout_duration': '00:18:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
  