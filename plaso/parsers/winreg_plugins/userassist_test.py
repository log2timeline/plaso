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
"""Tests for the UserAssist Windows Registry plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import userassist


class WindowsXPUserAssistPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows XP UserAssist Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = userassist.UserAssistPlugin3()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        u'\\{75048700-EF1F-11D0-9888-006097DEACF9}')
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 15)

    event_object = event_objects[0]

    # Tue Aug 4 15:11:22.811067 UTC 2009
    self.assertEquals(event_object.timestamp, 1249398682811067)

    regvalue_identifier = u'UEME_RUNPIDL:%csidl2%\\MSN.lnk'
    expected_value = u'[Count: 14]'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}\\Count] {1:s}: {2:s}'.format(
            key_path, regvalue_identifier, expected_value)
    # The short message contains the first 76 characters of the key path.
    expected_msg_short = u'[{0:s}...'.format(key_path[:76])

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class Windows7UserAssistPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows 7 UserAssist Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = userassist.UserAssistPlugin8()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        u'\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}')
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 63)

    event_object = event_objects[0]

    # Wed Nov 10 07:49:37.078067 UTC 2010
    self.assertEquals(event_object.timestamp, 1289375377078067)

    regvalue_identifier = u'Microsoft.Windows.GettingStarted'
    expected_value = (
        u'[userassist_entry: None, Count: 14, app_focus_count: 21, '
        u'focus_duration: 420000]')
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}\\Count] {1:s}: {2:s}'.format(
          key_path, regvalue_identifier, expected_value)
    # The short message contains the first 76 characters of the key path.
    expected_msg_short = u'[{0:s}...'.format(key_path[:76])

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
