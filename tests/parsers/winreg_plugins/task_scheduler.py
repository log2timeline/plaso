#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Task Scheduler Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import task_scheduler

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

    self.CheckTimestamp(event.timestamp, '2009-07-14 04:53:25.811618')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)
    self.assertEqual(event_data.data_type, 'task_scheduler:task_cache:entry')
    self.assertEqual(event_data.task_name, 'SynchronizeTime')
    self.assertEqual(
        event_data.task_identifier, '{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}')

    expected_message = (
        '[{0:s}] '
        'Task: SynchronizeTime '
        '[Identifier: {{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}}]').format(
            key_path)
    expected_short_message = (
        'Task: SynchronizeTime')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2009-07-14 05:08:50.811627')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.data_type, 'task_scheduler:task_cache:entry')

    expected_message = (
        '[{0:s}] '
        'Task: SynchronizeTime '
        '[Identifier: {{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}}]').format(
            key_path)
    expected_short_message = (
        'Task: SynchronizeTime')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
