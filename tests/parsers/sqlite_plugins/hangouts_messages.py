#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the hangouts messages plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import hangouts_messages

from tests.parsers.sqlite_plugins import test_lib


class HangoutsMessagesTest(test_lib.SQLitePluginTestCase):
  """Tests for the Hangouts message database plugin."""

  def testProcess(self):
    """Test the Process function on a Google hangouts file."""
    plugin = hangouts_messages.HangoutsMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['googlehangouts.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'body': 'How are you?',
        'data_type': 'android:messaging:hangouts',
        'message_status': 4,
        'message_type': 2,
        'sender': 'John Macron',
        'timestamp': '2017-07-17 04:41:54.326967',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
