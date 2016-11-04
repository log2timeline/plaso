#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android SMS plugin."""

import unittest

from plaso.formatters import android_sms  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_sms

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidSMSTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android SMS database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'mmssms.db'])
  def testProcess(self):
    """Test the Process function on an Android SMS mmssms.db file."""
    plugin_object = android_sms.AndroidSMSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'mmssms.db'], plugin_object)

    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    self.assertEqual(len(storage_writer.events), 9)

    # Check the first SMS sent.
    event_object = storage_writer.events[0]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-29 16:56:28.038')
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
