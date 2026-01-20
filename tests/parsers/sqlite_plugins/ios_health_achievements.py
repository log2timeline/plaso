#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Achievements SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_achievements

from tests.parsers.sqlite_plugins import test_lib


class IOSHealthAchievementsTest(test_lib.SQLitePluginTestCase):
  """Tests for iOS Health Achievements SQLite database plugin."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_health_achievements.IOSHealthAchievementsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['iOS_13_4_1_healthdb_secure.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 60)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_recovery_warnings = (
        storage_writer.GetNumberOfAttributeContainers('recovery_warning'))
    self.assertEqual(number_of_recovery_warnings, 0)

    expected_event_values = {
        'creator_device': 1,
        'created_date': '2020-03-27T00:00:00+00:00',
        'data_type': 'ios:health:achievements',
        'earned_date': '2020-03-27T00:00:00+00:00',
        'sync_provenance': 1,
        'template_unique_name': 'FirstWorkout-HKWorkoutActivityTypeRunning',
        'value_canonical_unit': None,
        'value_in_canonical_unit': None}

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
  