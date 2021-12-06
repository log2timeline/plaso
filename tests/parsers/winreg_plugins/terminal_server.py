#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Terminal Server Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import terminal_server

from tests.parsers.winreg_plugins import test_lib


class ServersTerminalServerClientPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client Windows Registry plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path (str): Windows Registry key path.
      time_string (str): key last written date and time.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Servers', key_path=key_path, last_written_time=filetime.timestamp,
        offset=865)

    server_subkey_name = 'myserver.com'
    server_subkey = dfwinreg_fake.FakeWinRegistryKey(
        server_subkey_name, last_written_time=filetime.timestamp, offset=1456)

    registry_key.AddSubkey(server_subkey_name, server_subkey)

    value_data = 'DOMAIN\\username'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'UsernameHint', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    server_subkey.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = terminal_server.TerminalServerClientPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
        'Servers')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
        'Default\\AddIns\\RDPDR')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
        'Servers')
    registry_key = self._CreateTestKey(key_path, '2012-08-28 09:23:49.002031')

    plugin = terminal_server.TerminalServerClientPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2012-08-28 09:23:49.0020310',
        'data_type': 'windows:registry:mstsc:connection',
        'key_path': '{0:s}\\myserver.com'.format(key_path),
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.NAME,
        'username': 'DOMAIN\\username'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2012-08-28 09:23:49.0020310',
        'data_type': 'windows:registry:key_value',
        'key_path': key_path,
        'values': None}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


class DefaultTerminalServerClientMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client MRU Windows Registry plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path (str): Windows Registry key path.
      time_string (str): key last written date and time.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Default', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_data = '192.168.16.60'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'MRU0', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = 'computer.domain.com'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'MRU1', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=612)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
        'Default')
    registry_key = self._CreateTestKey(key_path, '2012-08-28 09:23:49.002031')

    plugin = terminal_server.TerminalServerClientMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_entries = (
        'MRU0: 192.168.16.60 '
        'MRU1: computer.domain.com')

    expected_event_values = {
        'date_time': '2012-08-28 09:23:49.0020310',
        'data_type': 'windows:registry:mstsc:mru',
        'entries': expected_entries,
        'key_path': key_path,
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.NAME}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
