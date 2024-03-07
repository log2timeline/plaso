#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox downloads database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import firefox_downloads

from tests.parsers.sqlite_plugins import test_lib


class FirefoxDownloadsPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox downloads database plugin."""

  def testProcessVersion25(self):
    """Tests the Process function on a Firefox Downloads database file."""
    plugin = firefox_downloads.FirefoxDownloadsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['downloads.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:downloads:download',
        'end_time': '2013-07-18T19:01:18.578000+00:00',
        'full_path': 'file:///D:/plaso-static-1.0.1-win32-vs2008.zip',
        'received_bytes': 15974599,
        'start_time': '2013-07-18T18:59:59.312000+00:00',
        'total_bytes': 15974599,
        'url': (
            'https://plaso.googlecode.com/files/'
            'plaso-static-1.0.1-win32-vs2008.zip')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


  def testProcessVersion118(self):
    """Tests the Process function on a Firefox Downloads database file."""
    plugin = firefox_downloads.Firefox118DownloadsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['places118.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:downloads:download',
        'download_state': 1,
        'end_time': 1689722429974,
        'full_path':
        'file:///C:/Users/factdevteam/'
        'Downloads/VSCodeUserSetup-x64-1.80.1.exe',
        'name': 'VSCodeUserSetup-x64-1.80.1.exe',
        'received_bytes': 93176792,
        'start_time': "2023-07-18T23:20:28.452000+00:00",
        'total_bytes': 93176792,
        'type': 3,
        'url': (
            "https://az764295.vo.msecnd.net/stable/74f6148eb9ea00507ec"
            "113ec51c489d6ffb4b771/VSCodeUserSetup-x64-1.80.1.exe"
            )
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
