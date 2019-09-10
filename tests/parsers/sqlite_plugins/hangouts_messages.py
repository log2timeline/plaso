#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the hangouts messages plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import hangouts_messages as _  # pylint: disable=unused-import
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

    # Check the second message.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2017-07-17 04:41:54.326967')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.body, 'How are you?')
    self.assertEqual(event_data.message_status, 4)
    self.assertEqual(event_data.message_type, 2)
    self.assertEqual(event_data.sender, 'John Macron')

    expected_message = (
        'Sender: John Macron '
        'Body: How are you? '
        'Status: READ '
        'Type: RECEIVED')
    expected_short_message = 'How are you?'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
