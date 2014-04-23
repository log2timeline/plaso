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
"""Tests for the Microsoft Office MRUs Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import officemru
from plaso.parsers.winreg_plugins import test_lib


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Microsoft Office MRUs Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = officemru.OfficeMRUPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER-WIN7.DAT'])
    key_path = u'\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 5)

    event_object = event_objects[0]

    # Tue Mar 13 18:27:15.083000 UTC 2012
    self.assertEquals(event_object.timestamp, 1331663235083000)

    regvalue_identifier = u'Item 1'
    expected_value = (
        u'[F00000000][T01CD0146EA1EADB0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        u'SA-23E Mitchell-Hyundyne Starfury.docx')
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_msg_short = u'[{0:s}] {1:s}: [F00000000][T01CD0146...'.format(
        key_path, regvalue_identifier)
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
