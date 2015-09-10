#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the WinRAR Windows Registry plugin."""

import unittest

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.dfwinreg import fake as dfwinreg_fake
from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import winrar

from tests.parsers.winreg_plugins import test_lib


class WinRarArcHistoryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the WinRAR ArcHistory Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winrar.WinRarHistoryPlugin()

  def _GetTestRegistry(self):
    """Retrieves the Windows Registry for testing.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    values = []

    value_data = u'C:\\Downloads\\The Sleeping Dragon CD1.iso'.encode(
        u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'0', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    values.append(registry_value)

    value_data = u'C:\\Downloads\\plaso-static.rar'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'1', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=612)
    values.append(registry_value)

    key_path = u'\\Software\\WinRAR\\ArcHistory'
    filetime = dfwinreg_fake.Filetime()
    filetime.CopyFromString(u'2012-08-28 09:23:49.002031')
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'ArcHistory', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456, values=values)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    registry_key = self._GetTestRegistry()

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_key_path = u'\\Software\\WinRAR\\ArcHistory'
    expected_message = (
        u'[{0:s}] '
        u'0: C:\\Downloads\\The Sleeping Dragon CD1.iso '
        u'1: C:\\Downloads\\plaso-static.rar').format(expected_key_path)
    expected_message_short = (
        u'[{0:s}] '
        u'0: C:\\Downloads\\The Sleeping Dragon CD1.iso '
        u'1: ...').format(expected_key_path)
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
