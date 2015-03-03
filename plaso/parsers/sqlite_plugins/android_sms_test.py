#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android SMS plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import android_sms as android_sms_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import android_sms
from plaso.parsers.sqlite_plugins import test_lib


class AndroidSmsTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android SMS database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = android_sms.AndroidSmsPlugin()

  def testProcess(self):
    """Test the Process function on an Android SMS mmssms.db file."""
    test_file = self._GetTestFilePath(['mmssms.db'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    self.assertEqual(len(event_objects), 9)

    # Check the first SMS sent.
    event_object = event_objects[0]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-29 16:56:28.038')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_address = u'1 555-521-5554'
    self.assertEqual(event_object.address, expected_address)

    expected_body = u'Yo Fred this is my new number.'
    self.assertEqual(event_object.body, expected_body)

    expected_msg = (
        u'Type: SENT '
        u'Address: 1 555-521-5554 '
        u'Status: READ '
        u'Message: Yo Fred this is my new number.')
    expected_short = u'Yo Fred this is my new number.'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
