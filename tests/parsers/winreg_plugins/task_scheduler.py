#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Task Scheduler Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import task_scheduler

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class TaskCacheWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Task Cache key Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = task_scheduler.TaskCacheWindowsRegistryPlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
        'CurrentVersion\\Schedule\\TaskCache')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE-RunTests'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE-RunTests'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
        'CurrentVersion\\Schedule\\TaskCache')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = task_scheduler.TaskCacheWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 174)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.CheckTimestamp(event.timestamp, '2009-07-14 04:53:25.811618')

    regvalue_identifier = 'Task: SynchronizeTime'
    expected_value = '[ID: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]'
    self._TestRegvalue(event, regvalue_identifier, expected_value)

    expected_message = '[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2009-07-14 05:08:50.811627')

    regvalue_identifier = 'Task: SynchronizeTime'

    expected_message = (
        'Task: SynchronizeTime '
        '[Identifier: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]')
    expected_short_message = (
        'Task: SynchronizeTime')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
