#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""This file contains a test for the default plist parser."""

import os
import unittest

from plaso import plist
from plaso.lib import errors
from plaso.lib import plist_interface


class MockPlugin(plist_interface.PlistPlugin):
  """Mock plugin."""
  PLIST_PATH = 'plist_binary'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  def GetEntries(self):
    return True


class TestPlistInterface(unittest.TestCase):
  """The unit test for default plist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = 'test_data'
    self.fd = os.path.join(self.base_path, 'plist_binary')
    self.plugins = plist_interface.GetPlistPlugins()

  def testGetPlistPlugins(self):
    self.assertTrue(self.plugins)

  def testDefaultInList(self):
    self.assertTrue('DefaultPlugin' in [x.plugin_name for x in self.plugins])

  def testMockPluginErrors(self):
    """Ensure plugin proceeds only if both correct filename and keys exist."""
    plugin = MockPlugin(None)

    # Test correct filename and keys.
    self.assertTrue(
        plugin.Process('plist_binary', {'DeviceCache': 1, 'PairedDevices': 1}))

    # Correct filename with odd filename cAsinG.  Adding an extra useless key.
    self.assertTrue(
        plugin.Process('pLiSt_BinAry', {'DeviceCache': 1, 'PairedDevices': 1,
                                        'R@ndomExtraKey': 1}))
    # Test wrong filename.
    with self.assertRaises(errors.WrongPlistPlugin):
      plugin.Process('wrong_file.plist', {'DeviceCache': 1, 'PairedDevices': 1})

    # Test not enough required keys.
    with self.assertRaises(errors.WrongPlistPlugin):
      plugin.Process('plist_binary', {'Useless_Key': 0, 'PairedDevices': 1})


if __name__ == '__main__':
  unittest.main()
