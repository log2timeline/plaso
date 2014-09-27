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
"""Tests for the airport plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import airport
from plaso.parsers.plist_plugins import test_lib


class AirportPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the airport plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = airport.AirportPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['com.apple.airport.preferences.plist'])
    plist_name = 'com.apple.airport.preferences.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 4)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1375144166000000, 1386874984000000, 1386949546000000,
        1386950747000000])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[0]
    self.assertEqual(event_object.key, u'item')
    self.assertEqual(event_object.root, u'/RememberedNetworks')
    expected_desc = (
        u'[WiFi] Connected to network: <europa> using security '
        u'WPA/WPA2 Personal')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/RememberedNetworks/item {0:s}'.format(expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
