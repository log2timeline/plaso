#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Terminal Server Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
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

    server_subkey = dfwinreg_fake.FakeWinRegistryKey(
        'myserver.com', last_written_time=filetime.timestamp, offset=1456)

    value_data = 'DOMAIN\\username'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'UsernameHint', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    server_subkey.AddValue(registry_value)

    registry_key.AddSubkey(server_subkey)

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
    time_string = '2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = terminal_server.TerminalServerClientPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-08-28 09:23:49.002031')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)
    self.assertEqual(event_data.data_type, 'windows:registry:mstsc:connection')

    expected_message = (
        '[{0:s}\\myserver.com] '
        'Username hint: DOMAIN\\username').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2012-08-28 09:23:49.002031')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:registry:key_value')

    expected_message = (
        '[{0:s}] '
        '(empty)').format(key_path)

    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


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
    time_string = '2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = terminal_server.TerminalServerClientMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-08-28 09:23:49.002031')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)
    self.assertEqual(event_data.data_type, 'windows:registry:mstsc:mru')

    expected_message = (
        '[{0:s}] '
        'MRU0: 192.168.16.60 '
        'MRU1: computer.domain.com').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
