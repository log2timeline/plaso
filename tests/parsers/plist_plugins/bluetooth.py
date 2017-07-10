#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Bluetooth plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import bluetooth

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class TestBtPlugin(test_lib.PlistPluginTestCase):
  """Tests for the Bluetooth plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'plist_binary'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_name = u'plist_binary'
    plist_name = u'com.apple.bluetooth.plist'

    plugin = bluetooth.BluetoothPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [test_file_name], plist_name)

    self.assertEqual(storage_writer.number_of_events, 14)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    paired_events = []
    timestamps = []
    for event in events:
      timestamps.append(event.timestamp)
      if event.desc.startswith(u'Paired'):
        paired_events.append(event)

    # Ensure all 14 events and times from the plist are parsed correctly.
    self.assertEqual(len(timestamps), 14)

    expected_timestamps = frozenset([
        1341957896010535, 1341957896010535, 1350666385239661, 1350666391557044,
        1341957900020116, 1302199013524275, 1301012201414766, 1351818797324095,
        1351818797324095, 1351819298997672, 1351818803000000, 1351827808261762,
        1345251268370453, 1345251192528750])

    self.assertTrue(set(timestamps) == expected_timestamps)

    # Ensure two paired devices are matched.
    self.assertEqual(len(paired_events), 2)

    # One of the paired event descriptions should contain the string:
    # Paired:True Name:Apple Magic Trackpad 2.
    paired_descriptions = [
        event.desc for event in paired_events]

    self.assertTrue(
        u'Paired:True Name:Apple Magic Trackpad 2' in paired_descriptions)

    expected_string = (
        u'/DeviceCache/44-00-00-00-00-04 '
        u'Paired:True '
        u'Name:Apple Magic Trackpad 2')

    self._TestGetMessageStrings(event, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
