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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 102)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'background_time':  0.0,
        'bundle_identifier': 'com.apple.springboard.home-screen',
        'screen_on_time': 30.339694}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'background_time':  0.121086,
        'bundle_identifier': 'com.apple.Spotlight',
        'screen_on_time': 0.0}

    self.CheckEventValues(storage_writer, events[72], expected_event_values)


if __name__ == '__main__':
  unittest.main()
