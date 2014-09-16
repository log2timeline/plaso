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
"""Tests for the plist plugin interface."""

import unittest

from plaso.events import plist_event
from plaso.lib import errors
from plaso.lib import queue
# Register plist plugins.
from plaso.parsers import plist  # pylint: disable=unused-import
from plaso.parsers import manager
from plaso.parsers.plist_plugins import interface
from plaso.parsers.plist_plugins import test_lib


class MockPlugin(interface.PlistPlugin):
  """Mock plugin."""
  PLIST_PATH = 'plist_binary'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  def GetEntries(self, unused_parser_context, **unused_kwargs):
    yield plist_event.PlistEvent(
        u'/DeviceCache/44-00-00-00-00-00', u'LastInquiryUpdate',
        1351827808261762)


class TestPlistPlugin(test_lib.PlistPluginTestCase):
  """Tests for the plist plugin interface."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    event_queue = queue.SingleThreadedQueue()
    parse_error_queue = queue.SingleThreadedQueue()

    self._parser_context = self._GetParserContext(
        event_queue, parse_error_queue)

    self._top_level_dict = {
        'DeviceCache': {
            '44-00-00-00-00-04': {
                'Name': 'Apple Magic Trackpad 2', 'LMPSubversion': 796,
                'Services': '', 'BatteryPercent': 0.61},
            '44-00-00-00-00-02': {
                'Name': 'test-macpro', 'ClockOffset': 28180,
                'PageScanPeriod': 2, 'PageScanRepetitionMode': 1}}}

  def testGetRegisteredPlugins(self):
    """Tests the GetRegisteredPlugins function."""
    plugins = manager.ParsersManager.GetRegisteredPlugins(
        parent_class=interface.PlistPlugin)

    self.assertNotEquals(plugins, {})

    self.assertTrue('plist_default' in plugins.keys())

  def testProcess(self):
    """Tests the Process function."""
    # Ensure the plugin only processes if both filename and keys exist.
    mock_plugin = MockPlugin()

    # Test correct filename and keys.
    self.assertTrue(mock_plugin.Process(
        self._parser_context, plist_name='plist_binary', top_level={
        'DeviceCache': 1, 'PairedDevices': 1}))

    # Correct filename with odd filename cAsinG.  Adding an extra useless key.
    self.assertTrue(mock_plugin.Process(
        self._parser_context, plist_name='pLiSt_BinAry', top_level={
        'DeviceCache': 1, 'PairedDevices': 1, 'R@ndomExtraKey': 1}))

    # Test wrong filename.
    with self.assertRaises(errors.WrongPlistPlugin):
      mock_plugin.Process(
        self._parser_context, plist_name='wrong_file.plist', top_level={
          'DeviceCache': 1, 'PairedDevices': 1})

    # Test not enough required keys.
    with self.assertRaises(errors.WrongPlistPlugin):
      mock_plugin.Process(
        self._parser_context, plist_name='plist_binary', top_level={
          'Useless_Key': 0, 'PairedDevices': 1})

  def testRecurseKey(self):
    """Tests the RecurseKey function."""
    # Ensure with a depth of 1 we only return the root key.
    result = list(interface.RecurseKey(self._top_level_dict, depth=1))
    self.assertEquals(len(result), 1)

    # Trying again with depth limit of 2 this time.
    result = list(interface.RecurseKey(self._top_level_dict, depth=2))
    self.assertEquals(len(result), 3)

    # A depth of two should gives us root plus the two devices. Let's check.
    my_keys = []
    for unused_root, key, unused_value in result:
      my_keys.append(key)
    expected = set(['DeviceCache', '44-00-00-00-00-04', '44-00-00-00-00-02'])
    self.assertTrue(expected == set(my_keys))

  def testGetKeys(self):
    """Tests the GetKeys function."""
    # Match DeviceCache from the root level.
    key = ['DeviceCache']
    result = interface.GetKeys(self._top_level_dict, key)
    self.assertEquals(len(result), 1)

    # Look for a key nested a layer beneath DeviceCache from root level.
    # Note: overriding the default depth to look deeper.
    key = ['44-00-00-00-00-02']
    result = interface.GetKeys(self._top_level_dict, key, depth=2)
    self.assertEquals(len(result), 1)

    # Check the value of the result was extracted as expected.
    self.assertTrue('test-macpro' == result[key[0]]['Name'])


if __name__ == '__main__':
  unittest.main()
