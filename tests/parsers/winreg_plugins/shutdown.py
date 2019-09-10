#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the LastShutdown value plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import shutdown as _  # pylint: disable=unused-import
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
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-04-04 01:58:40.839250')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_SHUTDOWN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)

    self.assertEqual(event_data.value_name, 'ShutdownTime')

    expected_message = (
        '[{0:s}] '
        'Description: ShutdownTime').format(key_path)
    expected_short_message = 'ShutdownTime'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
