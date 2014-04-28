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
"""Tests for the CCleaner Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import ccleaner
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import winregistry


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the CCleaner Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = ccleaner.CCleanerPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER-CCLEANER.DAT'])
    key_path = u'\\Software\\Piriform\\CCleaner'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 17)

    event_object = event_objects[0]

    self.assertEquals(event_object.timestamp, 1373709794000000)

    regvalue_identifier = u'UpdateKey'
    expected_value = u'07/13/2013 10:03:14 AM'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_string = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[2]

    self.assertEquals(event_object.timestamp, 0)

    regvalue_identifier = u'(App)Delete Index.dat files'
    expected_value = u'True'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_string = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
