#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Terminal Server Windows Registry plugin."""

import unittest

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import terminal_server

from tests.dfwinreg import test_lib as dfwinreg_test_lib
from tests.parsers.winreg_plugins import test_lib


class ServersTerminalServerClientPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Terminal Server Client Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = terminal_server.TerminalServerClientPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Software\\Microsoft\\Terminal Server Client\\Servers'
    values = []

    values.append(dfwinreg_test_lib.TestRegValue(
        u'UsernameHint', u'DOMAIN\\username'.encode(u'utf_16_le'),
        dfwinreg_definitions.REG_SZ, offset=1892))

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')

    server_key_path = (
        u'\\Software\\Microsoft\\Terminal Server Client\\Servers\\myserver.com')
    server_key = dfwinreg_test_lib.TestRegKey(
        server_key_path, expected_timestamp, values, offset=1456)

    winreg_key = dfwinreg_test_lib.TestRegKey(
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

    values.append(dfwinreg_test_lib.TestRegValue(
        u'MRU0', u'192.168.16.60'.encode(u'utf_16_le'),
        dfwinreg_definitions.REG_SZ, offset=1892))
    values.append(dfwinreg_test_lib.TestRegValue(
        u'MRU1', u'computer.domain.com'.encode(u'utf_16_le'),
        dfwinreg_definitions.REG_SZ, 612))

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-28 09:23:49.002031')
    winreg_key = dfwinreg_test_lib.TestRegKey(
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
