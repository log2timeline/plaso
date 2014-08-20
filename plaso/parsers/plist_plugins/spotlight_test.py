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
"""Tests for the spotlight plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import spotlight
from plaso.parsers.plist_plugins import test_lib


class SpotlightPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the spotlight plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = spotlight.SpotlightPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['com.apple.spotlight.plist'])
    plist_name = 'com.apple.spotlight.plist'
    events = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 9)

    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
    expected_timestamps = frozenset([
        1379937262090906, 1387822901900937, 1375236414408299, 1388331212005129,
        1376696381196456, 1386951868185477, 1380942616952359, 1389056477460443,
        1386111811136093])
    self.assertTrue(set(timestamps) == expected_timestamps)

    event_object = event_objects[1]
    self.assertEqual(event_object.key, u'gr')
    self.assertEqual(event_object.root, u'/UserShortcuts')
    expected_desc = (u'Spotlight term searched "gr" associate to '
                     u'Grab (/Applications/Utilities/Grab.app)')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'/UserShortcuts/gr {}'.format(expected_desc)
    expected_short = expected_string[:77] + u'...'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
