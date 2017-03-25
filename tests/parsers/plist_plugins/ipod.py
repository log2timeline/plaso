#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the iPod plist plugin."""

import unittest

from plaso.formatters import ipod  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.plist_plugins import ipod

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class TestIPodPlugin(test_lib.PlistPluginTestCase):
  """Tests for the iPod plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.iPod.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.iPod.plist'

    plugin_object = ipod.IPodPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 4)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    event_object = events[0]

    timestamp = timelib.Timestamp.CopyFromString(u'1995-11-22 18:25:07')
    self.assertEqual(event_object.timestamp, timestamp)
    self.assertEqual(event_object.device_id, u'0000A11300000000')

    event_object = events[2]

    timestamp = timelib.Timestamp.CopyFromString(u'2013-10-09 19:27:54')
    self.assertEqual(event_object.timestamp, timestamp)

    expected_message = (
        u'Device ID: 4C6F6F6E65000000 '
        u'Type: iPhone [10016] '
        u'Connected 1 times '
        u'Serial nr: 526F676572 '
        u'IMEI [012345678901234]')
    expected_message_short = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_CONNECTED)

    self.assertEqual(event_object.device_class, u'iPhone')
    self.assertEqual(event_object.device_id, u'4C6F6F6E65000000')
    self.assertEqual(event_object.firmware_version, 256)
    self.assertEqual(event_object.imei, u'012345678901234')
    self.assertEqual(event_object.use_count, 1)


if __name__ == '__main__':
  unittest.main()
