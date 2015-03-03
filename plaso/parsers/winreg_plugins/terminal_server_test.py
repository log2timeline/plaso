#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Terminal Server Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import terminal_server
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import test_lib as winreg_test_lib


class ServersTerminalServerClientPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = terminal_server.TerminalServerClientPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Software\\Microsoft\\Terminal Server Client\\Servers'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'UsernameHint', 'DOMAIN\\username'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=1892))

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-28 09:23:49.002031')

    server_key_path = (
        u'\\Software\\Microsoft\\Terminal Server Client\\Servers\\myserver.com')
    server_key = winreg_test_lib.TestRegKey(
        server_key_path, expected_timestamp, values, offset=1456)

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, expected_timestamp, None, offset=865, subkeys=[server_key])

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = u'[{0:s}] UsernameHint: DOMAIN\\username'.format(key_path)
    expected_msg_short = (
        u'[{0:s}] UsernameHint: DOMAIN\\use...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class DefaultTerminalServerClientMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client MRU Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = terminal_server.TerminalServerClientMRUPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Software\\Microsoft\\Terminal Server Client\\Default'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'MRU0', '192.168.16.60'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=1892))
    values.append(winreg_test_lib.TestRegValue(
        'MRU1', 'computer.domain.com'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, 612))

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-28 09:23:49.002031')
    winreg_key = winreg_test_lib.TestRegKey(
        key_path, expected_timestamp, values, 1456)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = u'[{0:s}] MRU0: 192.168.16.60'.format(key_path)
    expected_msg_short = u'[{0:s}] MRU0: 192.168.16.60'.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    self.assertEqual(event_object.timestamp, 0)

    expected_msg = u'[{0:s}] MRU1: computer.domain.com'.format(key_path)
    expected_msg_short = u'[{0:s}] MRU1: computer.domain.com'.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
