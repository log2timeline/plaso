#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Timeline SQLite database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import windows_timeline

from tests.parsers.sqlite_plugins import test_lib


class WindowsTimelineTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows Timeline plugin."""

  def testProcess(self):
    """Tests the Process function on a Windows Timeline SQLite database."""
    plugin = windows_timeline.WindowsTimelinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['windows_timeline_ActivitiesCache.db'], plugin)

    self.assertEqual(112, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'active_duration_seconds': 9,
        'data_type': 'windows:timeline:user_engaged',
        'package_identifier': 'c:\\python34\\python.exe',
        'reporting_app': 'ShellActivityMonitor',
        'timestamp': '2018-08-03 11:29:00.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_START}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'active_duration_seconds': 11,
        'data_type': 'windows:timeline:user_engaged',
        'package_identifier': (
            'c:\\users\\demouser\\appdata\\local\\programs\\python\\'
            'python37-32\\python.exe'),
        'reporting_app': 'ShellActivityMonitor',
        'timestamp': '2018-07-27 11:58:55.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_START}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'application_display_name': 'OneDrive',
        'data_type': 'windows:timeline:generic',
        'description': '',
        'package_identifier': 'Microsoft.SkyDrive.Desktop',
        'timestamp': '2018-07-25 12:04:48.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_START}

    self.CheckEventValues(storage_writer, events[80], expected_event_values)

    expected_event_values = {
        'application_display_name': 'Notepad',
        'data_type': 'windows:timeline:generic',
        'description': 'C:\\Users\\demouser\\Desktop\\SCHEMA.txt',
        'package_identifier': (
            '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe'),
        'timestamp': '2018-07-27 12:36:09.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_START}

    self.CheckEventValues(storage_writer, events[96], expected_event_values)


if __name__ == '__main__':
  unittest.main()
