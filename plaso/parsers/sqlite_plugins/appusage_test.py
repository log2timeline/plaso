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
"""Tests for the Mac OS X application usage database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import appusage as appusage_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import test_lib
from plaso.parsers.sqlite_plugins import appusage


class ApplicationUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mac OS X application usage activity database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._plugin = appusage.ApplicationUsagePlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['application_usage.sqlite'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The sqlite database contains 5 events.
    self.assertEquals(len(event_objects), 5)

    # Check the first event.
    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-05-07 18:52:02')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.application, u'/Applications/Safari.app')
    self.assertEquals(event_object.app_version, u'9537.75.14')
    self.assertEquals(event_object.bundle_id, u'com.apple.Safari')
    self.assertEquals(event_object.count, 1)

    expected_msg = (
        u'/Applications/Safari.app v.9537.75.14 '
        u'(bundle: com.apple.Safari). '
        u'Launched: 1 time(s)')

    expected_msg_short = u'/Applications/Safari.app (1 time(s))'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
