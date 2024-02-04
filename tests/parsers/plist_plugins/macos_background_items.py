#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS background items plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macos_background_items

from tests.parsers.plist_plugins import test_lib


class MacOS1013BackgroundItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS backgrounditems.btm plist parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'backgrounditems.btm'

    plugin = macos_background_items.MacOS1013BackgroundItemsPlugin()
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
        'cnid_path': '/103/706090',
        'data_type': 'macos:background_items:entry',
        'name': 'Syncthing',
        'target_path': '/Applications/Syncthing.app',
        'volume_flags': 0x100000081,
        'volume_mount_point': '/',
        'volume_name': 'Macintosh HD'}
    # TODO: 'volume_flags': 'IsLocal, IsInternal, SupportsPersistentIDs'

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class MacOS13BackgroundItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS BackgroundItems-v4.btm plist parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'BackgroundItems-v4.btm'

    plugin = macos_background_items.MacOS13BackgroundItemsPlugin()
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
        'cnid_path': '/14578/55377',
        'data_type': 'macos:background_items:entry',
        'target_path': '/Applications/Syncthing.app',
        'volume_flags': 0x100000081,
        'volume_mount_point': '/',
        'volume_name': 'Macintosh HD'}
    # TODO: 'volume_flags': 'IsLocal, IsInternal, SupportsPersistentIDs'

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
