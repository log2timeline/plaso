#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iMessage plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import imessage as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import imessage

from tests.parsers.sqlite_plugins import test_lib


class IMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the iMessage database plugin."""

  def testProcess(self):
    """Test the Process function on a iMessage chat.db file."""
    plugin = imessage.IMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['imessage_chat.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    # Check the eighth message sent.
    event = events[7]

    self.CheckTimestamp(event.timestamp, '2015-11-30 10:48:40.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.imessage_id, 'xxxxxx2015@icloud.com')
    self.assertEqual(event_data.read_receipt, 1)
    self.assertEqual(event_data.message_type, 0)

    expected_text = 'Did you try to send me a message?'
    self.assertEqual(event_data.text, expected_text)

    expected_message = (
        'iMessage ID: xxxxxx2015@icloud.com '
        'Read Receipt: True '
        'Message Type: Received '
        'Service: iMessage '
        'Message Content: Did you try to send me a message?')
    expected_short_message = 'Did you try to send me a message?'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
