#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the Application Compatibility Cache key Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import event
from plaso.parsers.winreg_plugins import appcompatcache
from plaso.parsers.winreg_plugins import test_lib


class AppCompatCacheRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the AppCompatCache Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.current_control_set = 'ControlSet001'
    self._plugin = appcompatcache.AppCompatCachePlugin(pre_obj=pre_obj)

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['SYSTEM'])
    key_path = u'\\ControlSet001\\Control\\Session Manager\\AppCompatCache'
    winreg_key = self._GetKeyFromFile(test_file, key_path)

    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 331)

    event_object = event_objects[330]

    # TODO: fix after clean up CL is submitted.
    self.assertEquals(event_object.timestamp, 1333504720776749)

    expected_msg = (
        u'[{0:s}] '
        u'AppCompatCache: [Number of cached entries: 330]').format(key_path)

    expected_msg_short = (
        u'[{0:s}] AppCompatCache: [Numb...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[9]

    # TODO: fix after clean up CL is submitted.
    self.assertEquals(event_object.timestamp, 1333503997932964)

    expected_msg = (
        u'[{0:s}] '
        u'Cached entry: 10: [Path: \\??\\C:\\Windows\\PSEXESVC.EXE]').format(
            key_path)

    expected_msg_short = (
        u'[{0:s}] Cached entry: 10: [Pa...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

if __name__ == '__main__':
  unittest.main()
