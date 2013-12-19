#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a test for WinVers registry parsing in Plaso."""
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import winver
from plaso.winreg import test_lib


class TestWinVerRegistry(unittest.TestCase):
  """The unit test for WinVer registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        'ProductName', 'MyTestOS'.encode('utf_16_le'), 1, 123))
    values.append(test_lib.TestRegValue(
        'CSDBuildNumber', '5'.encode('utf_16_le'), 1, 1892))
    values.append(test_lib.TestRegValue(
        'RegisteredOwner', 'A Concerned Citizen'.encode('utf_16_le'), 1, 612))
    values.append(test_lib.TestRegValue('InstallDate', '\x13\x1aAP', 3, 1001))

    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Windows NT\\CurrentVersion', 1346445929000000, values,
        153)

  def testWinVer(self):
    """Test the WinVer plugin."""
    plugin = winver.WinVerPlugin(None, None, None)
    entries = list(plugin.Process(self.regkey))

    line = (u'[\\Microsoft\\Windows NT\\CurrentVersion]  Windows Version Infor'
            'mation:  Owner: A Concerned Citizen Product name: MyTestOS sp: 5')

    self.assertEquals(len(entries), 1)
    self.assertEquals(entries[0].timestamp, int(1346443795 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)


if __name__ == '__main__':
  unittest.main()
