#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android SMS plugin."""

import unittest

from plaso.formatters import android_sms  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_sms

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidSMSTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android SMS database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'mmssms.db'])
  def testProcess(self):
    """Test the Process function on an Android SMS mmssms.db file."""
    plugin = android_sms.AndroidSMSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'mmssms.db'], plugin)

    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    # Check the first SMS sent.
    event = events[0]

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-29 16:56:28.038')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_address = u'1 555-521-5554'
    self.assertEqual(event.address, expected_address)

    expected_body = u'Yo Fred this is my new number.'
    self.assertEqual(event.body, expected_body)

    expected_message = (
        u'Type: SENT '
        u'Address: 1 555-521-5554 '
        u'Status: READ '
        u'Message: Yo Fred this is my new number.')
    expected_short_message = u'Yo Fred this is my new number.'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
