#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS background items plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macos_background_items

from tests.parsers.plist_plugins import test_lib


class MacOSBackgroundItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS background items plist parser plugin."""

  def testProcessWithBackgroundItemsBtm(self):
    """Tests the Process function with a backgrounditems.btm file."""
    plist_name = 'backgrounditems.btm'

    plugin = macos_background_items.MacOSBackgroundItemsPlistPlugin()
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
        'data_type': 'macos:background_items:entry',
        'name': 'iTunesHelper',
        'target_creation_time': '2017-07-12T18:29:32.000000+00:00',
        'target_path': (
            '/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app'),
        'volume_creation_time': '2017-10-20T07:52:27.000000+00:00',
        'volume_flags': 0x100000081,
        'volume_mount_point': '/',
        'volume_name': 'Macintosh HD'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  # TODO: add tests for version 4, 7 or 8


if __name__ == '__main__':
  unittest.main()
