#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the default Windows Registry plugin."""

import unittest

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.dfwinreg import fake as dfwinreg_fake
from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import default

from tests.parsers.winreg_plugins import test_lib


class TestDefaultRegistry(test_lib.RegistryPluginTestCase):
  """Tests for the default Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = default.DefaultPlugin()

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfwinreg_fake.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'TimeZoneInformation', key_path=key_path,
        last_written_time=filetime.timestamp, offset=1456)

    value_data = u'acb'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'MRUList', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = u'Some random text here'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'a', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = u'c:/evil.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'b', data=value_data, data_type=dfwinreg_definitions.REG_BINARY,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = u'C:/looks_legit.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'c', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1001)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Microsoft\\Some Windows\\InterestingApp\\MRU'
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

    expected_msg = (
        u'[{0:s}] '
        u'MRUList: [REG_SZ] acb '
        u'a: [REG_SZ] Some random text here '
        u'b: [REG_BINARY] '
        u'c: [REG_SZ] C:/looks_legit.exe').format(key_path)

    expected_msg_short = (
        u'[{0:s}] MRUList: [REG_SZ] acb a: [REG_SZ...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
