#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iPod plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import ipod as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.plist_plugins import ipod

from tests.parsers.plist_plugins import test_lib


class TestIPodPlugin(test_lib.PlistPluginTestCase):
  """Tests for the iPod plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.iPod.plist'

    plugin = ipod.IPodPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '1995-11-22 18:25:07.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.device_id, '0000A11300000000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-10-09 19:27:54.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_CONNECTED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.device_class, 'iPhone')
    self.assertEqual(event_data.device_id, '4C6F6F6E65000000')
    self.assertEqual(event_data.firmware_version, 256)
    self.assertEqual(event_data.imei, '012345678901234')
    self.assertEqual(event_data.use_count, 1)

    expected_message = (
        'Device ID: 4C6F6F6E65000000 '
        'Type: iPhone [10016] '
        'Connected 1 times '
        'Serial nr: 526F676572 '
        'IMEI [012345678901234]')
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
