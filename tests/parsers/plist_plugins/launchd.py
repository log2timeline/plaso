#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS launchd plist plugin."""

import unittest

from plaso.parsers.plist_plugins import launchd

from tests.parsers.plist_plugins import test_lib


class MacOSLaunchdPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS launchd plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'launchd.plist'

    plugin = launchd.MacOSLaunchdPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

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
        'data_type': 'macos:launchd:entry',
        'group_name': 'nobody',
        'name': 'com.foobar.test',
        'program': '/Test --flag arg1',
        'user_name': 'nobody'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
