#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS login window plist plugin."""
import unittest

from plaso.parsers.plist_plugins import macos_login_window

from tests.parsers.plist_plugins import test_lib


class MacOSLoginWindowPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS login window plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'loginwindow.plist'

    plugin = macos_login_window.MacOSLoginWindowPlugin()
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
        'data_type': 'macos:login_window:managed_login_item',
        'is_hidden': True,
        'path': '/Applications/SafeConnect.app'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'macos:login_window:entry',
        'login_hook': '/Users/matthew/login.sh',
        'logout_hook': '/Users/matthew/logout.sh'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
