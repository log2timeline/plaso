#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS application usage database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import macos_appusage

from tests.parsers.sqlite_plugins import test_lib


class MacOSApplicationUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS application usage activity database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = macos_appusage.MacOSApplicationUsagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['application_usage.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application': '/Applications/Safari.app',
        'application_version': '9537.75.14',
        'bundle_identifier': 'com.apple.Safari',
        'count': 1,
        'data_type': 'macos:application_usage:entry',
        'event': 'launch',
        'last_used_time': '2014-05-07T18:52:02+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
