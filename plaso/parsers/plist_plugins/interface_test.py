#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the plist plugin interface."""

import unittest

from plaso.events import plist_event
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface
from plaso.parsers.plist_plugins import test_lib


class MockPlugin(interface.PlistPlugin):
  """Mock plugin."""

  NAME = u'mock_plist_plugin'
  DESCRIPTION = u'Parser for testing parsing plist files.'

  PLIST_PATH = u'plist_binary'
  PLIST_KEYS = frozenset([u'DeviceCache', u'PairedDevices'])

  def GetEntries(self, parser_mediator, **unused_kwargs):
    event_object = plist_event.PlistEvent(
        u'/DeviceCache/44-00-00-00-00-00', u'LastInquiryUpdate',
        1351827808261762)
    parser_mediator.ProduceEvent(event_object)


class TestPlistPlugin(test_lib.PlistPluginTestCase):
  """Tests for the plist plugin interface."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._top_level_dict = {
        u'DeviceCache': {
            u'44-00-00-00-00-04': {
                u'Name': u'Apple Magic Trackpad 2', u'LMPSubversion': 796,
                u'Services': u'', u'BatteryPercent': 0.61},
            u'44-00-00-00-00-02': {
                u'Name': u'test-macpro', u'ClockOffset': 28180,
                u'PageScanPeriod': 2, u'PageScanRepetitionMode': 1}}}

  def testGetPluginNames(self):
    """Tests the GetPluginNames function."""
    plugin_names = plist.PlistParser.GetPluginNames()

    self.assertNotEqual(plugin_names, [])

    self.assertTrue(u'plist_default' in plugin_names)

  def testProcess(self):
    """Tests the Process function."""
    # Ensure the plugin only processes if both filename and keys exist.
    plugin_object = MockPlugin()

    # Test correct filename and keys.
    top_level = {u'DeviceCache': 1, u'PairedDevices': 1}
    event_object_generator = self._ParsePlistWithPlugin(
        plugin_object, u'plist_binary', top_level)
    event_objects = self._GetEventObjectsFromQueue(event_object_generator)

    self.assertEqual(len(event_objects), 1)

    # Correct filename with odd filename cAsinG. Adding an extra useless key.
    top_level = {u'DeviceCache': 1, u'PairedDevices': 1, u'R@ndomExtraKey': 1}
    event_object_generator = self._ParsePlistWithPlugin(
        plugin_object, u'pLiSt_BinAry', top_level)
    event_objects = self._GetEventObjectsFromQueue(event_object_generator)

    self.assertEqual(len(event_objects), 1)

    # Test wrong filename.
    top_level = {u'DeviceCache': 1, u'PairedDevices': 1}
    with self.assertRaises(errors.WrongPlistPlugin):
      _ = self._ParsePlistWithPlugin(
          plugin_object, u'wrong_file.plist', top_level)

    # Test not enough required keys.
    top_level = {u'Useless_Key': 0, u'PairedDevices': 1}
    with self.assertRaises(errors.WrongPlistPlugin):
      _ = self._ParsePlistWithPlugin(
          plugin_object, u'plist_binary.plist', top_level)

  def testRecurseKey(self):
    """Tests the RecurseKey function."""
    # Ensure with a depth of 1 we only return the root key.
    result = list(interface.RecurseKey(self._top_level_dict, depth=1))
    self.assertEqual(len(result), 1)

    # Trying again with depth limit of 2 this time.
    result = list(interface.RecurseKey(self._top_level_dict, depth=2))
    self.assertEqual(len(result), 3)

    # A depth of two should gives us root plus the two devices. Let's check.
    my_keys = []
    for unused_root, key, unused_value in result:
      my_keys.append(key)
    expected = {u'DeviceCache', u'44-00-00-00-00-04', u'44-00-00-00-00-02'}
    self.assertTrue(expected == set(my_keys))

  def testGetKeys(self):
    """Tests the GetKeys function."""
    # Match DeviceCache from the root level.
    key = [u'DeviceCache']
    result = interface.GetKeys(self._top_level_dict, key)
    self.assertEqual(len(result), 1)

    # Look for a key nested a layer beneath DeviceCache from root level.
    # Note: overriding the default depth to look deeper.
    key = [u'44-00-00-00-00-02']
    result = interface.GetKeys(self._top_level_dict, key, depth=2)
    self.assertEqual(len(result), 1)

    # Check the value of the result was extracted as expected.
    self.assertTrue(u'test-macpro' == result[key[0]][u'Name'])


if __name__ == '__main__':
  unittest.main()
