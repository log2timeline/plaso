# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS powerlog database files."""

import unittest

from plaso.parsers.sqlite_plugins import ios_powerlog

from tests.parsers.sqlite_plugins import test_lib


class IOSPowerlogApplicationUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite parser plugin for iOS powerlog database files."""

  def testParse(self):
    """Tests the ParseApplicationRunTime method."""
    plugin = ios_powerlog.IOSPowerlogApplicationUsagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['powerlog_2021-12-16_05-54_84E2141B.PLSQL'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 102)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'background_time':  0.0,
        'bundle_identifier': 'com.apple.springboard.home-screen',
        'screen_on_time': 30.339694,
        'start_time': '2021-11-02T10:05:45+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
