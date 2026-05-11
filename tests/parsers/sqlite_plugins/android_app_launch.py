#!/usr/bin/env python3
"""Tests for the Android application launch database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_app_launch
from tests.parsers.sqlite_plugins import test_lib


class AndroidAppLaunchPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android application launch database plugin."""

  def testProcess(self):
    """Test the Process function on an Android SimpleStorage file."""
    plugin = android_app_launch.AndroidAppLaunchPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
       ['SimpleStorage'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 434)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'identifier': 2980,
        'launch_location_identifier': 4,
        'package_name': 'com.android.settings',
        'prediction_rank': -1,
        'prediction_source_identifier': 3,
        'prediction_ui_surface_identifier': 1,
        'start_time': '2022-12-04T16:59:28.274+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
