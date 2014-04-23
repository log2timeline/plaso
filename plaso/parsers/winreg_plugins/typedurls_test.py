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
"""Tests for the MSIE typed URLs Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import typedurls


__author__ = 'David Nides (david.nides@gmail.com)'


class MsieTypedURLsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the MSIE typed URLs Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = typedurls.TypedURLsPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER-WIN7.DAT'])
    key_path = u'\\Software\\Microsoft\\Internet Explorer\\TypedURLs'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 13)

    event_object = event_objects[0]

    # Mon Mar 12 21:23:53.307749 UTC 2012
    self.assertEquals(event_object.timestamp, 1331587433307749)

    regvalue_identifier = u'url1'
    expected_value = u'http://cnn.com/'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_string = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


class TypedPathsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the typed paths Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = typedurls.TypedURLsPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths')
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    # Wed Nov 10 07:58:15.811625 UTC 2010
    self.assertEquals(event_object.timestamp, 1289375895811625)

    regvalue_identifier = u'url1'
    expected_value = u'\\\\controller'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_msg_short = u'[{0:s}] {1:s}: \\\\cont...'.format(
        key_path, regvalue_identifier)
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
