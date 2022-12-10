#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Timeline SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import windows_timeline

from tests.parsers.sqlite_plugins import test_lib


class WindowsTimelineTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows Timeline plugin."""

  def testProcess(self):
    """Tests the Process function on a Windows Timeline SQLite database."""
    plugin = windows_timeline.WindowsTimelinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['windows_timeline_ActivitiesCache.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 112)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'active_duration_seconds': 9,
        'data_type': 'windows:timeline:user_engaged',
        'package_identifier': 'c:\\python34\\python.exe',
        'reporting_app': 'ShellActivityMonitor',
        'start_time': '2018-08-03T11:29:00+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'application_display_name': 'OneDrive',
        'data_type': 'windows:timeline:generic',
        'description': None,
        'package_identifier': 'Microsoft.SkyDrive.Desktop',
        'start_time': '2018-07-25T12:04:48+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 80)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
