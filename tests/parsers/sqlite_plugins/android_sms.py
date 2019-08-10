#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android SMS plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_sms as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import android_sms

from tests.parsers.sqlite_plugins import test_lib


class AndroidSMSTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android SMS database plugin."""

  def testProcess(self):
    """Test the Process function on an Android SMS mmssms.db file."""
    plugin = android_sms.AndroidSMSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['mmssms.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    # Check the first SMS sent.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-10-29 16:56:28.038000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.address, '1 555-521-5554')
    self.assertEqual(event_data.body, 'Yo Fred this is my new number.')

    expected_message = (
        'Type: SENT '
        'Address: 1 555-521-5554 '
        'Status: READ '
        'Message: Yo Fred this is my new number.')
    expected_short_message = 'Yo Fred this is my new number.'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
