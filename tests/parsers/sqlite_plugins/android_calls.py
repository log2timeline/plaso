#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Android SMS call history plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_calls as _  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import android_calls

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidCallSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Call History database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['contacts2.db'])
  def testProcess(self):
    """Test the Process function on an Android contacts2.db file."""
    plugin = android_calls.AndroidCallPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['contacts2.db'], plugin)

    # The contacts2 database file contains 5 events (MISSED/OUTGOING/INCOMING).
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # Check the first event.
    event = events[0]

    self.assertEqual(event.timestamp_desc, 'Call Started')

    self.CheckTimestamp(event.timestamp, '2013-11-06 21:17:16.690000')

    expected_number = '5404561685'
    self.assertEqual(event.number, expected_number)

    expected_type = 'MISSED'
    self.assertEqual(event.call_type, expected_type)

    expected_message = (
        'MISSED '
        'Number: 5404561685 '
        'Name: Barney '
        'Duration: 0 seconds')
    expected_short_message = 'MISSED Call'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2013-11-07 00:03:36.690000')

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2013-11-07 00:14:15.690000')

    self.assertEqual(event.timestamp_desc, 'Call Ended')

    self.assertEqual(event.duration, 639)


if __name__ == '__main__':
  unittest.main()
