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
"""This file contains the tests for the Outlook Registry plugins."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import outlook
from plaso.winreg import test_lib


class TestOutlookSearchMRUPlugin(unittest.TestCase):
  """The unit test for Outlook Search MRU Registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []

    values.append(test_lib.TestRegValue(
        ('C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
         'username@example.com.ost'), '\xcf\x2b\x37\x00',
        test_lib.TestRegValue.REG_DWORD, offset=1892))

    self.regkey = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Office\\15.0\\Outlook\\Search',
        1346145829002031, values, 1456)

  def testMSOutlook2013SearchMRUPlugin(self):
    """Run a simple test against a mocked key with values."""
    plugin = outlook.MSOutlook2013SearchMRUPlugin()
    generator = plugin.Process(self.regkey)
    self.assertTrue(generator)
    entries = list(generator)

    expected_msg = (
        u'[\\Software\\Microsoft\\Office\\15.0\\Outlook\\Search] '
        u'C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
        u'username@example.com.ost: 0x00372bcf')

    expected_msg_short = (
        u'[\\Software\\Microsoft\\Office\\15.0\\Outlook\\Search] '
        u'C:\\Users\\username\\AppData\\Lo...')

    self.assertEquals(len(entries), 1)
    self.assertEquals(entries[0].timestamp, 1346145829002031)

    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        entries[0])

    self.assertEquals(msg, expected_msg)
    self.assertEquals(msg_short, expected_msg_short)


class TestOutlookSearchCatalogMRUPlugin(unittest.TestCase):
  """The unit test for Outlook Search Catalog MRU Registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []

    values.append(test_lib.TestRegValue(
        ('C:\\Users\\username\\AppData\\Local\\Microsoft\\Outlook\\'
         'username@example.com.ost'), '\x94\x01\x00\x00\x00\x00',
        test_lib.TestRegValue.REG_BINARY, offset=827))

    self.regkey = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Office\\15.0\\Outlook\\Search\\Catalog',
        1346145829002031, values, 3421)

    # TODO: add test for Catalog key.


if __name__ == '__main__':
  unittest.main()
