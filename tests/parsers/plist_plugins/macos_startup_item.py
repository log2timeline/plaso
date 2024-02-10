#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS startup item plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macos_startup_item

from tests.parsers.plist_plugins import test_lib


class MacOSStartupItemPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS startup item plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'StartupParameters.plist'

    plugin = macos_startup_item.MacOSStartupItemPlugin()
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

    # Note that the startup item event data has no date and time attribute.
    expected_event_values = {
        'data_type': 'macos:startup_item:entry',
        'description': 'My Awesome Service',
        'order_preference': 'None',
        'provides': ['The best service ever'],
        'uses': ['Network', 'SystemLog']}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
