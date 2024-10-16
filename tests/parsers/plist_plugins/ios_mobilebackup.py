#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple iOS Car Play application plist plugin."""

import unittest

from plaso.parsers.plist_plugins import ios_mobilebackup

from tests.parsers.plist_plugins import test_lib


class IOSMobileBackupPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Apple iOS Car Play application plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.MobileBackup.plist'

    plugin = ios_mobilebackup.IOSMobileBackupPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 12)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_description': 'AccountEnabledDate',
        'data_type': 'ios:mobile:backup:entry',
        'activity_time': '2023-04-15T13:58:42.481633792+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
