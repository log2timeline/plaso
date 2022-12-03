#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Task Scheduler Windows Registry plugin."""

import unittest

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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 85)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'task_scheduler:task_cache:entry',
        'key_path': key_path,
        'last_registered_time': '2009-07-14T05:08:50.8116269+00:00',
        'last_written_time': '2009-07-14T04:53:25.8116181+00:00',
        'launch_time': None,
        'task_name': 'SynchronizeTime',
        'task_identifier': '{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}',
        'unknown_time': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
