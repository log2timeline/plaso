#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a test for UserAssist parsing in Plaso."""
import os
import re
import unittest

from plaso.lib import eventdata
from plaso.lib import win_registry
from plaso.parsers import winreg
from plaso.registry import test_lib
from plaso.registry import xpuserassist


class RegistryXPUserAssistTest(unittest.TestCase):
  """The unit test for XP UserAssist parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'NTUSER.DAT')
    file_object = open(test_file, 'rb')
    self.registry = win_registry.WinRegistry(file_object)

  def testUserAssist(self):
    """Test the user assist plugin."""
    key = self.registry.GetKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        '\\{75048700-EF1F-11D0-9888-006097DEACF9}\\Count')
    plugin = xpuserassist.XPUserAssistPlugin(None)
    entries = list(plugin.Process(key))

    self.assertEquals(entries[0].timestamp, 1249398682811067)
    self.assertTrue(
        u'UEME_RUNPIDL:%csidl2%\\MSN.lnk' in entries[0].regvalue)
    self.assertEquals(entries[0].regvalue[u'UEME_RUNPIDL:%csidl2%\\MSN.lnk'],
                      u'[Count: 14]')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(
        msg, u'UEME_RUNPIDL:%csidl2%\\MSN.lnk: [Count: 14]')


if __name__ == '__main__':
  unittest.main()
