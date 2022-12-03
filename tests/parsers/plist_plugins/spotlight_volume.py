#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Spotlight Volume configuration plist plugin."""

import unittest

from plaso.parsers.plist_plugins import spotlight_volume

from tests.parsers.plist_plugins import test_lib


class SpotlightVolumeConfigurationPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Spotlight Volume configuration plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'VolumeConfiguration.plist'

    plugin = spotlight_volume.SpotlightVolumeConfigurationPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2013-06-25T05:54:43.000000+00:00',
        'data_type': 'spotlight_volume_configuration:store',
        'partial_path': '/.MobileBackups',
        'volume_identifier': '4D4BFEB5-7FE6-4033-AAAA-AAAABBBBCCCCDDDD'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
