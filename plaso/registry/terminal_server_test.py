#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains the tests for the Terminal Server Registry plugins."""

import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.registry import terminal_server
from plaso.winreg import test_lib


class TestTerminalServerClientPlugin(unittest.TestCase):
  """The unit test for Terminal Server Client Registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []

    values.append(test_lib.TestRegValue(
        'UsernameHint', 'DOMAIN\\username'.encode('utf_16_le'),
        test_lib.TestRegValue.REG_SZ, offset=1892))

    server_key = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Terminal Server Client\\Servers\\myserver.com',
        1346145829002031, values, offset=1456)

    self.regkey = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Terminal Server Client\\Servers',
        1346145829002031, None, offset=865, subkeys=[server_key])

  def testServersTerminalServerClientPlugin(self):
    """Run a simple test against a mocked key with values."""
    plugin = terminal_server.ServersTerminalServerClientPlugin(
        None, None, None)
    generator = plugin.Process(self.regkey)
    self.assertTrue(generator)
    entries = list(generator)

    expected_line1 = (
        u'[\\Software\\Microsoft\\Terminal Server Client\\Servers] '
        u'UsernameHint: DOMAIN\\username')

    self.assertEquals(len(entries), 1)
    self.assertEquals(entries[0].timestamp, 1346145829002031)

    msg1, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])

    self.assertEquals(msg1, expected_line1)


class TestTerminalServerClientMRU(unittest.TestCase):
  """The unit test for Terminal Server Client MRU Registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []

    values.append(test_lib.TestRegValue(
        'MRU0', '192.168.16.60'.encode('utf_16_le'),
        test_lib.TestRegValue.REG_SZ, offset=1892))
    values.append(test_lib.TestRegValue(
        'MRU1', 'computer.domain.com'.encode('utf_16_le'),
        test_lib.TestRegValue.REG_SZ, 612))

    self.regkey = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Terminal Server Client\\Default',
        1346145829002031, values, 1456)

  def testDefaulTerminalServerClientMRUPlugin(self):
    """Run a simple test against a mocked key with values."""
    plugin = terminal_server.DefaulTerminalServerClientMRUPlugin(
        None, None, None)
    generator = plugin.Process(self.regkey)
    self.assertTrue(generator)
    entries = list(generator)

    expected_line1 = (
        u'[\\Software\\Microsoft\\Terminal Server Client\\Default] '
        u'MRU0: 192.168.16.60')
    expected_line2 = (
        u'[\\Software\\Microsoft\\Terminal Server Client\\Default] '
        u'MRU1: computer.domain.com')

    self.assertEquals(len(entries), 2)
    self.assertEquals(entries[0].timestamp, 1346145829002031)
    self.assertEquals(entries[1].timestamp, 0)

    msg1, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    msg2, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])

    self.assertEquals(msg1, expected_line1)
    self.assertEquals(msg2, expected_line2)


if __name__ == '__main__':
  unittest.main()
