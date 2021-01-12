#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the LastShutdown value plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.winreg_plugins import shutdown

from tests.parsers.winreg_plugins import test_lib


class ShutdownWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the LastShutdown value plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = shutdown.ShutdownWindowsRegistryPlugin()

    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Windows'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Windows'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = shutdown.ShutdownWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'windows:registry:shutdown',
        'key_path': key_path,
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.plugin_name,
        'timestamp': '2012-04-04 01:58:40.839250',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_SHUTDOWN,
        'value_name': 'ShutdownTime'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
