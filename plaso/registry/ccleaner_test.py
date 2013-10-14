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
"""This file contains a test for CCleaner plugin in Plaso."""
import os
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.registry import ccleaner
from plaso.winreg import winpyregf

__author__ = 'Marc Seguin (segumarc@gmail.com)'


class RegistryCCleanerTest(unittest.TestCase):
  """The unit test for the CCleaner plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'NTUSER-CCLEANER.DAT')
    file_object = open(test_file, 'rb')
    self.registry = winpyregf.WinRegistry(file_object)

  def testCCleaner(self):
    """Test the CCleaner plugin."""
    key = self.registry.GetKey(
        '\\Software\\Piriform\\CCleaner')
    plugin = ccleaner.CCleanerPlugin(None, None, None)
    entries = list(plugin.Process(key))

    self.assertEquals(entries[0].timestamp, 1373709794000000)
    self.assertTrue(
        u'UpdateKey' in entries[0].regvalue)

    self.assertEquals(entries[0].regvalue[u'UpdateKey'],
                      u'07/13/2013 10:03:14 AM')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(
        msg, (u'[\\Software\\Piriform\\CCleaner]'
              ' UpdateKey: 07/13/2013 10:03:14 AM'))

    self.assertEquals(entries[2].timestamp, 0)
    self.assertTrue(
        u'(App)Delete Index.dat files' in entries[2].regvalue)

    self.assertEquals(entries[2].regvalue[u'(App)Delete Index.dat files'],
                      u'True')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[2])
    self.assertEquals(
        msg, (u'[\\Software\\Piriform\\CCleaner]'
              ' (App)Delete Index.dat files: True'))

if __name__ == '__main__':
  unittest.main()
