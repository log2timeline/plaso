#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the WinVer Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import winver
from plaso.winreg import test_lib as winreg_test_lib


class WinVerPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the WinVer Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winver.WinVerPlugin()

  def testWinVer(self):
    """Test the WinVer plugin."""
    key_path = u'\\Microsoft\\Windows NT\\CurrentVersion'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        u'ProductName', u'MyTestOS'.encode(u'utf_16_le'), 1, 123))
    values.append(winreg_test_lib.TestRegValue(
        u'CSDBuildNumber', u'5'.encode(u'utf_16_le'), 1, 1892))
    values.append(winreg_test_lib.TestRegValue(
        u'RegisteredOwner', u'A Concerned Citizen'.encode(u'utf_16_le'),
        1, 612))
    values.append(winreg_test_lib.TestRegValue(
        u'InstallDate', b'\x13\x1aAP', 3, 1001))

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1346445929000000, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-31 20:09:55')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Note that the double spaces here are intentional.
    expected_msg = (
        u'[{0:s}]  '
        u'Windows Version Information:  '
        u'Owner: A Concerned Citizen '
        u'Product name: MyTestOS sp: 5').format(key_path)

    expected_msg_short = (
        u'[{0:s}]  '
        u'Windows Version Information:  '
        u'Owner: ...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)
    # TODO: Write a test for a non-synthetic key


if __name__ == '__main__':
  unittest.main()
