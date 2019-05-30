#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Timeline plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import windows_timeline

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib

class WindowsTimelineTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows Timeline plugin."""

  @shared_test_lib.skipUnlessHasTestFile([
      'windows_timeline_ActivitiesCache.db'])
  def testProcess(self):
    """Tests the Process function on a Windows Timeline db."""

    plugin = windows_timeline.WindowsTimelinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['windows_timeline_ActivitiesCache.db'], plugin)

    self.assertEqual(112, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())
    event = events[0]

    self.assertEqual('windows:timeline:user_engaged', event.data_type)
    self.CheckTimestamp(event.timestamp, '2018-08-03 11:29:00.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)
    self.assertEqual(9, event.active_duration_seconds)
    self.assertEqual('ShellActivityMonitor', event.reporting_app)
    self.assertEqual('c:\\python34\\python.exe', event.package_identifier)

    expected_long_message = (
        'Package Identifier: c:\\python34\\python.exe '
        'Active Duration (seconds): 9 Reporting App: ShellActivityMonitor')
    expected_short_message = 'c:\\python34\\python.exe'
    self._TestGetMessageStrings(
        event, expected_long_message, expected_short_message)

    event = events[2]
    self.assertEqual('windows:timeline:user_engaged', event.data_type)
    self.CheckTimestamp(event.timestamp, '2018-07-27 11:58:55.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)
    self.assertEqual(11, event.active_duration_seconds)
    self.assertEqual('ShellActivityMonitor', event.reporting_app)
    self.assertEqual(
        'c:\\users\\demouser\\appdata\\local\\programs\\python\\python37-32\\'
        'python.exe', event.package_identifier)

    expected_long_message = (
        'Package Identifier: c:\\users\\demouser\\appdata'
        '\\local\\programs\\python\\python37-32\\python.exe Active Duration ('
        'seconds): 11 Reporting App: ShellActivityMonitor')
    expected_short_message = (
        'c:\\users\\demouser\\appdata\\local\\programs\\'
        'python\\python37-32\\python.exe')
    self._TestGetMessageStrings(
        event, expected_long_message, expected_short_message)

    event = events[80]
    self.assertEqual('windows:timeline:generic', event.data_type)
    self.CheckTimestamp(event.timestamp, '2018-07-25 12:04:48.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)
    self.assertEqual('Microsoft.SkyDrive.Desktop', event.package_identifier)
    self.assertEqual('', event.description)
    self.assertEqual('OneDrive', event.application_display_name)

    expected_long_message = (
        'Application Display Name: OneDrive Package '
        'Identifier: Microsoft.SkyDrive.Desktop')
    expected_short_message = 'Microsoft.SkyDrive.Desktop'
    self._TestGetMessageStrings(
        event, expected_long_message, expected_short_message)

    event = events[96]
    self.assertEqual('windows:timeline:generic', event.data_type)
    self.CheckTimestamp(event.timestamp, '2018-07-27 12:36:09.000000')
    self.assertEqual(
        definitions.TIME_DESCRIPTION_START, event.timestamp_desc)
    self.assertEqual(
        '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe',
        event.package_identifier)
    self.assertEqual(
        'C:\\Users\\demouser\\Desktop\\SCHEMA.txt', event.description)
    self.assertEqual('Notepad', event.application_display_name)

    expected_long_message = (
        'Application Display Name: Notepad Package Identifier: '
        '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe Description:'
        ' C:\\Users\\demouser\\Desktop\\SCHEMA.txt')
    expected_short_message = (
        '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\notepad.exe')
    self._TestGetMessageStrings(
        event, expected_long_message, expected_short_message)

if __name__ == '__main__':
  unittest.main()
