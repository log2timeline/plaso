#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS login items plist plugin."""
import unittest

from plaso.parsers.plist_plugins import macos_login_items

from tests.parsers.plist_plugins import test_lib


class MacOS1012LoginItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS launchd plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.loginitems.plist'

    plugin = macos_login_items.MacOS1012LoginItemsPlugin()
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

    expected_path = '/Applications/iTunes.app/Contents/MacOS/iTunesHelper.app'
    expected_event_values = {
        'data_type': 'macos:loginitems:entry',
        'name': 'iTunesHelper',
        'hidden': True,
        'cnid_path': '67899/67877/67876/71',
        'volume_name': 'Macintosh HD',
        'target_path': expected_path,
        'volume_mount_point': '/',
        'volume_flags': 'IsBootVolume, HasPersistentFileIds'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class MacOS1013LoginItemsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS launchd plist plugin."""

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
  """Tests for the MacOS launchd plist plugin."""

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
