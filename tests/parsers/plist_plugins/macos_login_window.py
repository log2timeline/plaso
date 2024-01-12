#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS login window plist plugin."""
import unittest

from plaso.parsers.plist_plugins import macos_login_window

from tests.parsers.plist_plugins import test_lib


class MacOSLoginWindowPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS login window plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'loginwindow.plist'

    plugin = macos_login_window.MacOSLoginWindowPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_autolaunch_event = {
        'data_type': 'macos:login_window:auto_launched_application',
        'hidden': True,
        'path': '/Applications/SafeConnect.app',
    }
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_autolaunch_event)

    expected_login_hook_event = {
        'data_type': 'macos:login_window:hook',
        'path': '/Users/matthew/login.sh',
        'hook_type': 'login',
    }
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_login_hook_event)

    expected_logout_hook_event = {
        'data_type': 'macos:login_window:hook',
        'path': '/Users/matthew/logout.sh',
        'hook_type': 'logout',
    }
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_logout_hook_event)


if __name__ == '__main__':
  unittest.main()
