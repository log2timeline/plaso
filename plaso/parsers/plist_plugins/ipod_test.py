#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the iPod plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import ipod as ipod_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import plist
from plaso.parsers.plist_plugins import ipod
from plaso.parsers.plist_plugins import test_lib


class TestIPodPlugin(test_lib.PlistPluginTestCase):
  """Tests for the iPod plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = ipod.IPodPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.iPod.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 4)

    event_object = event_objects[1]

    timestamp = timelib_test.CopyStringToTimestamp('2013-10-09 19:27:54')
    self.assertEquals(event_object.timestamp, timestamp)

    expected_string = (
        u'Device ID: 4C6F6F6E65000000 Type: iPhone [10016] Connected 1 times '
        u'Serial nr: 526F676572 IMEI [012345678901234]')

    self._TestGetMessageStrings(
        event_object, expected_string, expected_string[0:77] + '...')

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_CONNECTED)

    self.assertEquals(event_object.device_class, u'iPhone')
    self.assertEquals(event_object.device_id, u'4C6F6F6E65000000')
    self.assertEquals(event_object.firmware_version, 256)
    self.assertEquals(event_object.imei, u'012345678901234')
    self.assertEquals(event_object.use_count, 1)

    event_object = event_objects[3]
    timestamp = timelib_test.CopyStringToTimestamp('1995-11-22 18:25:07')
    self.assertEquals(event_object.timestamp, timestamp)
    self.assertEquals(event_object.device_id, u'0000A11300000000')


if __name__ == '__main__':
  unittest.main()
