#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

import unittest

from plaso.formatters import msie_webcache as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.esedb_plugins import msie_webcache
from plaso.parsers.esedb_plugins import test_lib


class MsieWebCacheEseDbPluginTest(test_lib.EseDbPluginTestCase):
  """Tests for the MSIE WebCache ESE database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = msie_webcache.MsieWebCacheEseDbPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_name = u'WebCacheV01.dat'
    event_queue_consumer = self._ParseEseDbFileWithPlugin(
        [test_file_name], self._plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1354)

    event_object = event_objects[0]

    self.assertEqual(event_object.container_identifier, 1)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-12 07:30:25.486198')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    expected_msg = (
        u'Container identifier: 1 '
        u'Set identifier: 0 '
        u'Name: Content '
        u'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        u'INetCache\\IE\\ '
        u'Table: Container_1')
    expected_msg_short = (
        u'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        u'INetCache\\IE\\')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
