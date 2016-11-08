#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the timemachine plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import timemachine

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class TimeMachinePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the timemachine plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.TimeMachine.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.TimeMachine.plist'

    plugin_object = timemachine.TimeMachinePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 13)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    expected_timestamps = [
        1379165051000000, 1380098455000000, 1380810276000000, 1381883538000000,
        1382647890000000, 1383351739000000, 1384090020000000, 1385130914000000,
        1386265911000000, 1386689852000000, 1387723091000000, 1388840950000000,
        1388842718000000]
    timestamps = sorted([event_object.timestamp for event_object in events])

    self.assertEqual(timestamps, expected_timestamps)

    event_object = events[0]
    self.assertEqual(event_object.root, u'/Destinations')
    self.assertEqual(event_object.key, u'item/SnapshotDates')

    expected_description = (
        u'TimeMachine Backup in BackUpFast '
        u'(5B33C22B-A4A1-4024-A2F5-C9979C4AAAAA)')
    self.assertEqual(event_object.desc, expected_description)

    expected_message = u'/Destinations/item/SnapshotDates {0:s}'.format(
        expected_description)
    expected_message_short = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
