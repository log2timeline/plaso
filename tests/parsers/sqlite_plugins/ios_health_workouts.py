#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        ['healthdb_secure.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    self.assertEqual(
        storage_writer.GetNumberOfAttributeContainers('extraction_warning'), 0)
    self.assertEqual(
        storage_writer.GetNumberOfAttributeContainers('recovery_warning'), 0)

    expected_event_values = {
        'activity_type': 'HKWorkoutActivityTypeRunning',
        'data_type': 'ios:health:workouts',
        'date_time': '2023-10-27T10:00:00+00:00',
        'duration': 1800.0,
        'duration_in_minutes': 30.0,
        'end_date_str': '2023-10-27T10:30:00+00:00',
        'goal': '5.0',
        'goal_type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
        'start_date_str': '2023-10-27T10:00:00+00:00',
        'total_basal_energy_burned': 50.5,
        'total_distance_km': 5.0,
        'total_distance_miles': 3.106855,
        'total_energy_burned': 350.0,
        'total_flights_climbed': 2.0,
        'total_w_steps': 6000.0,
        'workout_duration': '00:30:00'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'activity_type', None) ==
          'HKWorkoutActivityTypeRunning' and
          getattr(event_data, 'total_w_steps', None) == 6000.0):
        matched_index = i
        break

    msg = 'Golden workout event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
