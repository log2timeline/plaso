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
"""Tests for the bluetooth plist plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.lib import event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import bt
from plaso.parsers.plist_plugins import test_lib


class TestBtPlugin(test_lib.PlistPluginTestCase):
  """Tests for the bluetooth plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = bt.BtPlugin(None)
    self._parser = plist.PlistParser(event.PreprocessObject(), None)

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['plist_binary'])
    plist_name = 'com.apple.bluetooth.plist'
    events = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 14)

    paired_event_objects = []
    timestamps = []
    for event_object in event_objects:
      timestamps.append(event_object.timestamp)
      if event_object.desc.startswith(u'Paired'):
        paired_event_objects.append(event_object)

    # Ensure all 14 events and times from the plist are parsed correctly.
    self.assertEquals(len(timestamps), 14)

    expected_timestamps = frozenset([
        1341957896010535, 1341957896010535, 1350666385239661, 1350666391557044,
        1341957900020116, 1302199013524275, 1301012201414766, 1351818797324095,
        1351818797324095, 1351819298997672, 1351818803000000, 1351827808261762,
        1345251268370453, 1345251192528750])

    self.assertTrue(set(timestamps) == expected_timestamps)

    # Ensure two paired devices are matched.
    self.assertEquals(len(paired_event_objects), 2)

    # One of the paired event object descriptions should contain the string:
    # Paired:True Name:Apple Magic Trackpad 2.
    paired_descriptions = [
        event_object.desc for event_object in paired_event_objects]

    self.assertTrue(
        'Paired:True Name:Apple Magic Trackpad 2' in paired_descriptions)

    expected_string = (
        u'/DeviceCache/44-00-00-00-00-04 '
        u'Paired:True '
        u'Name:Apple Magic Trackpad 2')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
