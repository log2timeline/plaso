#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the default Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import default

from tests.parsers.winreg_plugins import test_lib


class TestDefaultRegistry(test_lib.RegistryPluginTestCase):
  """Tests for the default Windows Registry plugin."""

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
        'TimeZoneInformation', key_path=key_path,
        last_written_time=filetime.timestamp, offset=1456)

    value_data = 'acb'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'MRUList', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = 'Some random text here'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'a', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = 'c:/evil.exe'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'b', data=value_data, data_type=dfwinreg_definitions.REG_BINARY,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = 'C:/looks_legit.exe'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'c', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1001)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = '\\Microsoft\\Some Windows\\InterestingApp\\MRU'
    time_string = '2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = default.DefaultPlugin()
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

    expected_message = (
        '[{0:s}] '
        'MRUList: [REG_SZ] acb '
        'a: [REG_SZ] Some random text here '
        'b: [REG_BINARY] (22 bytes) '
        'c: [REG_SZ] C:/looks_legit.exe').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
