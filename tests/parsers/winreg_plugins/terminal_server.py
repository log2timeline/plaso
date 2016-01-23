#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Terminal Server Windows Registry plugin."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake
from dfwinreg import filetime as dfwinreg_filetime

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import terminal_server

from tests.parsers.winreg_plugins import test_lib


class ServersTerminalServerClientPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client Windows Registry plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = terminal_server.TerminalServerClientPlugin()

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfwinreg_filetime.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Servers', key_path=key_path, last_written_time=filetime.timestamp,
        offset=865)

    server_subkey = dfwinreg_fake.FakeWinRegistryKey(
        u'myserver.com', last_written_time=filetime.timestamp, offset=1456)

    value_data = u'DOMAIN\\username'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'UsernameHint', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    server_subkey.AddValue(registry_value)

    registry_key.AddSubkey(server_subkey)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
        u'Servers')
    time_string = u'2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}\\myserver.com] '
        u'Username hint: DOMAIN\\username').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    event_object = event_objects[1]

    expected_message = (
        u'[{0:s}] '
        u'myserver.com: DOMAIN\\username').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class DefaultTerminalServerClientMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client MRU Windows Registry plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = terminal_server.TerminalServerClientMRUPlugin()

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfwinreg_filetime.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Default', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_data = u'192.168.16.60'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'MRU0', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = u'computer.domain.com'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'MRU1', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=612)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
        u'Default')
    time_string = u'2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'MRU0: 192.168.16.60 '
        u'MRU1: computer.domain.com').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
