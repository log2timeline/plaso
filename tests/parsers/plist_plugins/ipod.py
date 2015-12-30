#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the iPod plist plugin."""

import unittest

from plaso.formatters import ipod as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import ipod

from tests.parsers.plist_plugins import test_lib


class TestIPodPlugin(test_lib.PlistPluginTestCase):
  """Tests for the iPod plist plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = ipod.IPodPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.iPod.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 4)

    event_object = event_objects[1]

    timestamp = timelib.Timestamp.CopyFromString(u'2013-10-09 19:27:54')
    self.assertEqual(event_object.timestamp, timestamp)

    expected_string = (
        u'Device ID: 4C6F6F6E65000000 Type: iPhone [10016] Connected 1 times '
        u'Serial nr: 526F676572 IMEI [012345678901234]')

    self._TestGetMessageStrings(
        event_object, expected_string, expected_string[0:77] + '...')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_CONNECTED)

    self.assertEqual(event_object.device_class, u'iPhone')
    self.assertEqual(event_object.device_id, u'4C6F6F6E65000000')
    self.assertEqual(event_object.firmware_version, 256)
    self.assertEqual(event_object.imei, u'012345678901234')
    self.assertEqual(event_object.use_count, 1)

    event_object = event_objects[3]
    timestamp = timelib.Timestamp.CopyFromString(u'1995-11-22 18:25:07')
    self.assertEqual(event_object.timestamp, timestamp)
    self.assertEqual(event_object.device_id, u'0000A11300000000')


if __name__ == '__main__':
  unittest.main()
