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
"""This file contains the tests for the WinRAR Registry plugins."""
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import winrar
from plaso.winreg import test_lib


class TestWinRarRegistry(unittest.TestCase):
  """The unit test for WinRAR Registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        '0', 'C:\\Downloads\\The Sleeping Dragon CD1.iso'.encode('utf_16_le'),
        test_lib.TestRegValue.REG_SZ, offset=1892))
    values.append(test_lib.TestRegValue(
        '1', 'C:\\Downloads\\plaso-static.rar'.encode('utf_16_le'),
        test_lib.TestRegValue.REG_SZ, offset=612))

    self.regkey = test_lib.TestRegKey(
        '\\Software\\WinRAR\\ArcHistory', 1346145829002031,
        values, offset=1456)

  def testWinRarArcHistoryPlugin(self):
    """Run a simple test against a mocked key with values."""
    plugin = winrar.WinRarArcHistoryPlugin(None, None, None)
    generator = plugin.Process(self.regkey)
    self.assertTrue(generator)
    entries = list(generator)

    expected_line1 = (
        u'[\\Software\\WinRAR\\ArcHistory] '
        u'0: C:\\Downloads\\The Sleeping Dragon CD1.iso')
    expected_line2 = (
        u'[\\Software\\WinRAR\\ArcHistory] '
        u'1: C:\\Downloads\\plaso-static.rar')

    self.assertEquals(len(entries), 2)
    self.assertEquals(entries[0].timestamp, 1346145829002031)
    self.assertEquals(entries[1].timestamp, 0)

    msg1, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    msg2, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])

    self.assertEquals(msg1, expected_line1)
    self.assertEquals(msg2, expected_line2)


if __name__ == '__main__':
  unittest.main()
