#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iPod, iPad and iPhone storage plist plugin."""

import unittest

from plaso.parsers.plist_plugins import ipod

from tests.parsers.plist_plugins import test_lib


class TestIPodPlugin(test_lib.PlistPluginTestCase):
  """Tests for the iPod, iPad and iPhone storage plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.iPod.plist'

    plugin = ipod.IPodPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'ipod:device:entry',
        'device_class': 'iPhone',
        'device_identifier': '4C6F6F6E65000000',
        'family_identifier': 10016,
        'firmware_version': '7.0',
        'imei': '012345678901234',
        'last_connected_time': '2013-10-09T19:27:54.000000+00:00',
        'serial_number': '526F676572',
        'use_count': 1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
