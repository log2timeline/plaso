#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the plist plugin interface."""

from __future__ import unicode_literals

import unittest

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers.plist_plugins import interface

from tests.parsers.plist_plugins import test_lib


class MockPlugin(interface.PlistPlugin):
  """Mock plugin."""

  NAME = 'mock_plist_plugin'
  DESCRIPTION = 'Parser for testing parsing plist files.'

  PLIST_PATH = 'plist_binary'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, **unused_kwargs):
    """Extracts entries for testing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    event_data = plist_event.PlistTimeEventData()
    event_data.key = 'LastInquiryUpdate'
    event_data.root = '/DeviceCache/44-00-00-00-00-00'

    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=1351827808261762)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class TestPlistPlugin(test_lib.PlistPluginTestCase):
  """Tests for the plist plugin interface."""

  # pylint: disable=protected-access

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._top_level_dict = {
        'DeviceCache': {
            '44-00-00-00-00-04': {
                'Name': 'Apple Magic Trackpad 2', 'LMPSubversion': 796,
                'Services': '', 'BatteryPercent': 0.61},
            '44-00-00-00-00-02': {
                'Name': 'test-macpro', 'ClockOffset': 28180,
                'PageScanPeriod': 2, 'PageScanRepetitionMode': 1}}}

  def testGetKeys(self):
    """Tests the _GetKeys function."""
    # Ensure the plugin only processes if both filename and keys exist.
    plugin = MockPlugin()

    # Match DeviceCache from the root level.
    key = ['DeviceCache']
    result = plugin._GetKeys(self._top_level_dict, key)
    self.assertEqual(len(result), 1)

    # Look for a key nested a layer beneath DeviceCache from root level.
    # Note: overriding the default depth to look deeper.
    key = ['44-00-00-00-00-02']
    result = plugin._GetKeys(self._top_level_dict, key, depth=2)
    self.assertEqual(len(result), 1)

    # Check the value of the result was extracted as expected.
    self.assertEqual(result[key[0]]['Name'], 'test-macpro')

  def testProcess(self):
    """Tests the Process function."""
    # Ensure the plugin only processes if both filename and keys exist.
    plugin = MockPlugin()

    # Test correct filename and keys.
    top_level = {'DeviceCache': 1, 'PairedDevices': 1}
    storage_writer = self._ParsePlistWithPlugin(
        plugin, 'plist_binary', top_level)

    self.assertEqual(storage_writer.number_of_events, 1)

    # Correct filename with odd filename cAsinG. Adding an extra useless key.
    top_level = {'DeviceCache': 1, 'PairedDevices': 1, 'R@ndomExtraKey': 1}
    storage_writer = self._ParsePlistWithPlugin(
        plugin, 'pLiSt_BinAry', top_level)

    self.assertEqual(storage_writer.number_of_events, 1)

    # Test wrong filename.
    top_level = {'DeviceCache': 1, 'PairedDevices': 1}
    with self.assertRaises(errors.WrongPlistPlugin):
      _ = self._ParsePlistWithPlugin(
          plugin, 'wrong_file.plist', top_level)

    # Test not enough required keys.
    top_level = {'Useless_Key': 0, 'PairedDevices': 1}
    with self.assertRaises(errors.WrongPlistPlugin):
      _ = self._ParsePlistWithPlugin(
          plugin, 'plist_binary.plist', top_level)

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
    expected = {'DeviceCache', '44-00-00-00-00-04', '44-00-00-00-00-02'}
    self.assertTrue(expected == set(my_keys))


if __name__ == '__main__':
  unittest.main()
