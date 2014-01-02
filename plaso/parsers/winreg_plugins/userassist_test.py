#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""This file contains tests for the UserAssist plugin."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import userassist
from plaso.pvfs import utils
from plaso.winreg import winregistry


class WindowsXPUserAssistTest(unittest.TestCase):
  """Test for parsing a Windows XP UserAssist Registry key."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'NTUSER.DAT')
    file_entry = utils.OpenOSFileEntry(test_file)
    self.winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testUserAssistPlugin3(self):
    """Test the Active Desktop (version 3) UserAssist plugin."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        '\\{75048700-EF1F-11D0-9888-006097DEACF9}')
    plugin = userassist.UserAssistPlugin3()
    entries = list(plugin.Process(key))

    self.assertEquals(len(entries), 15)
    self.assertEquals(entries[0].timestamp, 1249398682811067)
    self.assertTrue(
        u'UEME_RUNPIDL:%csidl2%\\MSN.lnk' in entries[0].regvalue)

    expected_value = (
        u'[Count: 14]')

    self.assertEquals(
        entries[0].regvalue[u'UEME_RUNPIDL:%csidl2%\\MSN.lnk'],
        expected_value)

    expected_string = (
        u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        u'\\{75048700-EF1F-11D0-9888-006097DEACF9}\\Count] '
        u'UEME_RUNPIDL:%csidl2%\\MSN.lnk: [Count: 14]')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_string)


class Windows7UserAssistTest(unittest.TestCase):
  """Test for parsing a Windows 7 UserAssist Registry key."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_entry = utils.OpenOSFileEntry(test_file)
    self.winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testUserAssistPlugin8(self):
    """Test the user assist plugin."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        '\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}')
    plugin = userassist.UserAssistPlugin8()
    entries = list(plugin.Process(key))

    self.assertEquals(len(entries), 63)
    self.assertEquals(entries[0].timestamp, 1289375377078067)
    self.assertTrue(
        u'Microsoft.Windows.GettingStarted' in entries[0].regvalue)

    expected_value = (
        u'[userassist_entry: None, Count: 14, app_focus_count: 21, '
        u'focus_duration: 420000]')

    self.assertEquals(
        entries[0].regvalue[u'Microsoft.Windows.GettingStarted'],
        expected_value)

    expected_string = (
      u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
      u'\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}\\Count] '
      u'Microsoft.Windows.GettingStarted: [userassist_entry: None, '
      u'Count: 14, app_focus_count: 21, focus_duration: 420000]')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_string)


if __name__ == '__main__':
  unittest.main()
