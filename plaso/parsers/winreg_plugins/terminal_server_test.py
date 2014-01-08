#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the Terminal Server Windows Registry plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import terminal_server
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import test_lib as winreg_test_lib


class ServersTerminalServerClientPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the erminal Server Client Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = terminal_server.ServersTerminalServerClientPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Software\\Microsoft\\Terminal Server Client\\Servers'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'UsernameHint', 'DOMAIN\\username'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=1892))

    server_key_path = (
        u'\\Software\\Microsoft\\Terminal Server Client\\Servers\\myserver.com')
    server_key = winreg_test_lib.TestRegKey(
        server_key_path, 1346145829002031, values, offset=1456)

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1346145829002031, None, offset=865, subkeys=[server_key])

    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEquals(event_object.timestamp, 1346145829002031)

    expected_msg = u'[{0:s}] UsernameHint: DOMAIN\\username'.format(key_path)
    expected_msg_short = (
        u'[{0:s}] UsernameHint: DOMAIN\\use...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class DefaulTerminalServerClientMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the erminal Server Client MRU Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = terminal_server.DefaulTerminalServerClientMRUPlugin()

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

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1346145829002031, values, 1456)

    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 2)

    event_object = event_objects[0]

    # Tue Aug 28 09:23:49.002031 UTC 2012
    self.assertEquals(event_object.timestamp, 1346145829002031)

    expected_msg = u'[{0:s}] MRU0: 192.168.16.60'.format(key_path)
    expected_msg_short = u'[{0:s}] MRU0: 192.168.16.60'.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    self.assertEquals(event_object.timestamp, 0)

    expected_msg = u'[{0:s}] MRU1: computer.domain.com'.format(key_path)
    expected_msg_short = u'[{0:s}] MRU1: computer.domain.com'.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
