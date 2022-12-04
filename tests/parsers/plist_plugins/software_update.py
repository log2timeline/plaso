#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Software Update plist plugin."""

import unittest

from plaso.parsers.plist_plugins import software_update

from tests.parsers.plist_plugins import test_lib


class MacOSSoftwareUpdatePlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the SoftwareUpdate plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.SoftwareUpdate.plist'

    plugin = software_update.MacOSSoftwareUpdatePlistPlugin()
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
        'data_type': 'macos:software_updata:entry',
        'full_update_time': '2014-01-06T17:43:48.000000+00:00',
        'recommended_updates': ['RAWCameraUpdate5.03 (031-2664)'],
        'system_version': '10.9.1 (13B42)',
        'update_time': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
