#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Timeline plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import windows_timeline

from tests.parsers.sqlite_plugins import test_lib


class WindowsTimelineTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows Timeline plugin."""

  def testProcess(self):
    """Tests the Process function on a Windows Timeline db."""

    plugin = windows_timeline.WindowsTimelinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['windows_timeline_ActivitiesCache.db'], plugin)

    self.assertEqual(112, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2018-08-03 11:29:00.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:timeline:user_engaged')
    self.assertEqual(event_data.active_duration_seconds, 9)
    self.assertEqual(event_data.reporting_app, 'ShellActivityMonitor')
    self.assertEqual(event_data.package_identifier, 'c:\\python34\\python.exe')

    expected_long_message = (
        'Package Identifier: c:\\python34\\python.exe '
        'Active Duration (seconds): 9 Reporting App: ShellActivityMonitor')
    expected_short_message = 'c:\\python34\\python.exe'
    self._TestGetMessageStrings(
        event_data, expected_long_message, expected_short_message)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2018-07-27 11:58:55.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:timeline:user_engaged')
    self.assertEqual(event_data.active_duration_seconds, 11)
    self.assertEqual(event_data.reporting_app, 'ShellActivityMonitor')
    expected_package_identifier = (
        'c:\\users\\demouser\\appdata\\local\\programs\\python\\python37-32\\'
        'python.exe')
    self.assertEqual(event_data.package_identifier, expected_package_identifier)

    expected_long_message = (
        'Package Identifier: c:\\users\\demouser\\appdata'
        '\\local\\programs\\python\\python37-32\\python.exe Active Duration ('
        'seconds): 11 Reporting App: ShellActivityMonitor')
    expected_short_message = (
        'c:\\users\\demouser\\appdata\\local\\programs\\'
        'python\\python37-32\\python.exe')
    self._TestGetMessageStrings(
        event_data, expected_long_message, expected_short_message)

    event = events[80]

    self.CheckTimestamp(event.timestamp, '2018-07-25 12:04:48.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:timeline:generic')
    self.assertEqual(
        event_data.package_identifier, 'Microsoft.SkyDrive.Desktop')
    self.assertEqual(event_data.description, '')
    self.assertEqual(event_data.application_display_name, 'OneDrive')

    expected_long_message = (
        'Application Display Name: OneDrive Package '
        'Identifier: Microsoft.SkyDrive.Desktop')
    expected_short_message = 'Microsoft.SkyDrive.Desktop'
    self._TestGetMessageStrings(
        event_data, expected_long_message, expected_short_message)

    event = events[96]

    self.CheckTimestamp(event.timestamp, '2018-07-27 12:36:09.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:timeline:generic')
    self.assertEqual(
        event_data.package_identifier,
        '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe')
    self.assertEqual(
        event_data.description, 'C:\\Users\\demouser\\Desktop\\SCHEMA.txt')
    self.assertEqual(event_data.application_display_name, 'Notepad')

    expected_long_message = (
        'Application Display Name: Notepad Package Identifier: '
        '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe Description:'
        ' C:\\Users\\demouser\\Desktop\\SCHEMA.txt')
    expected_short_message = (
        '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe')
    self._TestGetMessageStrings(
        event_data, expected_long_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
