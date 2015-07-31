#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the WinRAR Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import winrar

from tests.parsers.winreg_plugins import test_lib
from tests.winregistry import test_lib as winreg_test_lib


class WinRarArcHistoryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the WinRAR ArcHistory Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winrar.WinRarHistoryPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Software\\WinRAR\\ArcHistory'

    values = []

    binary_data = u'C:\\Downloads\\The Sleeping Dragon CD1.iso'.encode(
        u'utf_16_le')
    values.append(winreg_test_lib.TestRegValue(
        u'0', binary_data, winreg_test_lib.TestRegValue.REG_SZ, offset=1892))

    binary_data = u'C:\\Downloads\\plaso-static.rar'.encode(u'utf_16_le')
    values.append(winreg_test_lib.TestRegValue(
        u'1', binary_data, winreg_test_lib.TestRegValue.REG_SZ, offset=612))

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, expected_timestamp, values, offset=1456)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'[{0:s}] 0: C:\\Downloads\\The Sleeping Dragon CD1.iso').format(
            key_path)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[1]

    self.assertEqual(event_object.timestamp, 0)

    expected_string = u'[{0:s}] 1: C:\\Downloads\\plaso-static.rar'.format(
        key_path)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
