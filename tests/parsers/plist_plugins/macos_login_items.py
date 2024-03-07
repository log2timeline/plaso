#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS login items plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macos_login_items

from tests.parsers.plist_plugins import test_lib


class MacOSLoginItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS login items plist parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.loginitems.plist'

    plugin = macos_login_items.MacOSLoginItemsPlistPlugin()
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
        'data_type': 'macos:login_items:entry',
        'name': 'iTunesHelper',
        'hidden': True,
        'target_creation_time': '2018-03-26T04:33:05+00:00',
        'target_path': (
            '/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app'),
        'volume_creation_time': '2016-10-08T17:34:06+00:00',
        'volume_flags': 0x920,
        'volume_mount_point': '/',
        'volume_name': 'Macintosh HD'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
