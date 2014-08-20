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
"""Tests for the timemachine plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import timemachine
from plaso.parsers.plist_plugins import test_lib


class TimeMachinePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the timemachine plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = timemachine.TimeMachinePlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['com.apple.TimeMachine.plist'])
    plist_name = 'com.apple.timemachine.plist'
    events = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 13)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1379165051000000, 1380098455000000, 1380810276000000, 1381883538000000,
        1382647890000000, 1383351739000000, 1384090020000000, 1385130914000000,
        1386265911000000, 1386689852000000, 1387723091000000, 1388840950000000,
        1388842718000000])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[0]
    self.assertEqual(event_object.root, u'/Destinations')
    self.assertEqual(event_object.key, u'item/SnapshotDates')
    expected_desc = (
        u'TimeMachine Backup in BackUpFast '
        u'(5B33C22B-A4A1-4024-A2F5-C9979C4AAAAA)')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/Destinations/item/SnapshotDates {}'.format(
        expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
