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
"""Tests for the WinRAR Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import winrar
from plaso.winreg import test_lib as winreg_test_lib


class WinRarArcHistoryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the WinRAR ArcHistory Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winrar.WinRarHistoryPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Software\\WinRAR\\ArcHistory'

    values = []
    values.append(winreg_test_lib.TestRegValue(
        '0', 'C:\\Downloads\\The Sleeping Dragon CD1.iso'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=1892))
    values.append(winreg_test_lib.TestRegValue(
        '1', 'C:\\Downloads\\plaso-static.rar'.encode('utf_16_le'),
        winreg_test_lib.TestRegValue.REG_SZ, offset=612))

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1346145829002031, values, offset=1456)

    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 2)

    event_object = event_objects[0]

    # Tue Aug 28 09:23:49.002031 UTC 2012
    self.assertEquals(event_object.timestamp, 1346145829002031)

    expected_string = (
        u'[{0:s}] 0: C:\\Downloads\\The Sleeping Dragon CD1.iso').format(
            key_path)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[1]

    self.assertEquals(event_object.timestamp, 0)

    expected_string = u'[{0:s}] 1: C:\\Downloads\\plaso-static.rar'.format(
        key_path)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
