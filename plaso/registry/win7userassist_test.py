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
"""This file contains a test for Win7UserAssist parsing in Plaso."""
import os
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.registry import win7userassist
from plaso.winreg import winpyregf

__author__ = 'David Nides (david.nides@gmail.com)'


class RegistryWin7UserAssistTest(unittest.TestCase):
  """The unit test for Win7 UserAssist parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_object = open(test_file, 'rb')
    # TODO: create a factory not have a specific back-end implementation
    # directly invoked here.
    self.registry = winpyregf.WinRegistry(file_object)

  def testUserAssist(self):
    """Test the user assist plugin."""
    key = self.registry.GetKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}\\Count')
    plugin = win7userassist.Win7UserAssistPlugin2(None, None, None)
    entries = list(plugin.Process(key))

    self.assertEquals(entries[0].timestamp, 1289375377078067)
    self.assertTrue(
        u'Microsoft.Windows.GettingStarted' in entries[0].regvalue)
    self.assertEquals(entries[0].regvalue[u'Microsoft.Windows.GettingStarted'],
                      u'[userassist_entry: None, Count: 14, app_focus_count:'
                      ' 21, focus_duration: 420000]')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(
        msg, u'Microsoft.Windows.GettingStarted: [userassist_entry: None, '
        'Count: 14, app_focus_count: 21, focus_duration: 420000]')


if __name__ == '__main__':
  unittest.main()
