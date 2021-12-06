#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SAM Users Account information plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.winreg_plugins import sam_users

from tests.parsers.winreg_plugins import test_lib


class SAMUsersWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests the SAM Users Account information plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = sam_users.SAMUsersWindowsRegistryPlugin()

    key_path = 'HKEY_LOCAL_MACHINE\\SAM\\SAM\\Domains\\Account\\Users'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['SAM'])
    key_path = 'HKEY_LOCAL_MACHINE\\SAM\\SAM\\Domains\\Account\\Users'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = sam_users.SAMUsersWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'account_rid': 500,
        'comments': 'Built-in account for administering the computer/domain',
        'date_time': '2014-09-24 03:36:06.3588374',
        'data_type': 'windows:registry:sam_users',
        'login_count': 6,
        'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
        'username': 'Administrator'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test SAMUsersWindowsRegistryEvent.
    expected_event_values = {
        'account_rid': 500,
        'comments': 'Built-in account for administering the computer/domain',
        'date_time': '2010-11-20 21:48:12.5692440',
        'data_type': 'windows:registry:sam_users',
        'login_count': 6,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_LOGIN,
        'username': 'Administrator'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
