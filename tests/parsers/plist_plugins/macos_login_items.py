#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS login items plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macos_login_items

from tests.parsers.plist_plugins import test_lib


class MacOSLoginItemsAliasDataPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS login items with AliasData plist parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.loginitems.plist'

    plugin = macos_login_items.MacOSLoginItemsAliasDataPlistPlugin()
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
        'cnid_path': '3203382/3203360/3203359/85',
        'data_type': 'macos:login_item:entry',
        'name': 'iTunesHelper',
        'hidden': True,
        'target_path': (
            '/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app'),
        'volume_flags': 0x920,
        'volume_mount_point': '/',
        'volume_name': 'Macintosh HD'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class MacOS1013LoginItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS backgrounditems.btm plist parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'backgrounditems.btm'

    plugin = macos_login_items.MacOS1013LoginItemsPlugin()
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
        'data_type': 'macos:loginitems:entry',
        'name': 'Syncthing',
        'cnid_path': '/103/706090',
        'volume_name': 'Macintosh HD',
        'target_path': '/Applications/Syncthing.app',
        'volume_mount_point': '/',
        'volume_flags': 'IsLocal, IsInternal, SupportsPersistentIDs'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class MacOS13LoginItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS BackgroundItems-v4.btm plist parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'BackgroundItems-v4.btm'

    plugin = macos_login_items.MacOS13LoginItemsPlugin()
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
        'data_type': 'macos:loginitems:entry',
        'cnid_path': '/14578/55377',
        'volume_name': 'Macintosh HD',
        'target_path': '/Applications/Syncthing.app',
        'volume_mount_point': '/',
        'volume_flags': 'IsLocal, IsInternal, SupportsPersistentIDs'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
