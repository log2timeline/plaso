#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the iMessage plugin."""

import unittest

from plaso.formatters import imessage  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import imessage

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class IMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the iMessage database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'imessage_chat.db'])
  def testProcess(self):
    """Test the Process function on a iMessage chat.db file."""
    plugin = imessage.IMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'imessage_chat.db'], plugin)

    # The iMessage database file contains 10 events.
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    # Check the eighth message sent.
    event = events[7]

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-11-30 10:48:40.000')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.imessage_id, u'xxxxxx2015@icloud.com')
    self.assertEqual(event.read_receipt, 1)
    self.assertEqual(event.message_type, 0)

    expected_text = u'Did you try to send me a message?'
    self.assertEqual(event.text, expected_text)

    expected_message = (
        u'iMessage ID: xxxxxx2015@icloud.com '
        u'Read Receipt: True '
        u'Message Type: Received '
        u'Service: iMessage '
        u'Message Content: Did you try to send me a message?')
    expected_short_message = u'Did you try to send me a message?'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
