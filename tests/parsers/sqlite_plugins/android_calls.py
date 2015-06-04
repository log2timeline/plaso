#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android SMS call history plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import android_calls as android_calls_formatter
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_calls

from tests.parsers.sqlite_plugins import test_lib


class AndroidCallSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Call History database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = android_calls.AndroidCallPlugin()

  def testProcess(self):
    """Test the Process function on an Android contacts2.db file."""
    test_file = self._GetTestFilePath([u'contacts2.db'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The contacts2 database file contains 5 events (MISSED/OUTGOING/INCOMING).
    self.assertEqual(len(event_objects), 5)

    # Check the first event.
    event_object = event_objects[0]

    self.assertEqual(event_object.timestamp_desc, u'Call Started')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-06 21:17:16.690')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-06 21:17:16.690')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_number = u'5404561685'
    self.assertEqual(event_object.number, expected_number)

    expected_type = u'MISSED'
    self.assertEqual(event_object.call_type, expected_type)

    expected_call = (
        u'MISSED '
        u'Number: 5404561685 '
        u'Name: Barney '
        u'Duration: 0 seconds')
    expected_short = u'MISSED Call'
    self._TestGetMessageStrings(event_object, expected_call, expected_short)

    # Run some tests on the last 2 events.
    event_object_3 = event_objects[3]
    event_object_4 = event_objects[4]

    # Check the timestamp_desc of the last event.
    self.assertEqual(event_object_4.timestamp_desc, u'Call Ended')

    expected_timestamp3 = timelib.Timestamp.CopyFromString(
        u'2013-11-07 00:03:36.690')
    self.assertEqual(event_object_3.timestamp, expected_timestamp3)

    expected_timestamp4 = timelib.Timestamp.CopyFromString(
        u'2013-11-07 00:14:15.690')
    self.assertEqual(event_object_4.timestamp, expected_timestamp4)

    # Ensure the difference in btw. events 3 and 4 equals the duration.
    expected_duration, _ = divmod(
        expected_timestamp4 - expected_timestamp3, 1000000)
    self.assertEqual(event_object_4.duration, expected_duration)


if __name__ == '__main__':
  unittest.main()
