#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the timemachine plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import timemachine

from tests.parsers.plist_plugins import test_lib


class TimeMachinePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the timemachine plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.TimeMachine.plist'

    plugin = timemachine.TimeMachinePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 13)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1379165051000000, 1380098455000000, 1380810276000000, 1381883538000000,
        1382647890000000, 1383351739000000, 1384090020000000, 1385130914000000,
        1386265911000000, 1386689852000000, 1387723091000000, 1388840950000000,
        1388842718000000]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    event = events[0]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.root, '/Destinations')
    self.assertEqual(event_data.key, 'item/SnapshotDates')

    expected_description = (
        'TimeMachine Backup in BackUpFast '
        '(5B33C22B-A4A1-4024-A2F5-C9979C4AAAAA)')
    self.assertEqual(event_data.desc, expected_description)

    expected_message = '/Destinations/item/SnapshotDates {0:s}'.format(
        expected_description)
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
