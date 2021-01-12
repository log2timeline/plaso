#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iMessage plugin."""

import unittest

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

    expected_event_values = {
        'data_type': 'imessage:event:chat',
        'imessage_id': 'xxxxxx2015@icloud.com',
        'message_type': 0,
        'read_receipt': 1,
        'service': 'iMessage',
        'text': 'Did you try to send me a message?',
        'timestamp': '2015-11-30 10:48:40.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)


if __name__ == '__main__':
  unittest.main()
