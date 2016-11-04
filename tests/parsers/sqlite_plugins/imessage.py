#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the iMessage plugin."""

import unittest

from plaso.formatters import imessage  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import imessage

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class IMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the iMessage database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'imessage_chat.db'])
  def testProcess(self):
    """Test the Process function on a iMessage chat.db file."""
    plugin_object = imessage.IMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'imessage_chat.db'], plugin_object)

    # The iMessage database file contains 10 events.
    self.assertEqual(len(storage_writer.events), 10)

    # Check the eighth message sent.
    event_object = storage_writer.events[7]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-11-30 10:48:40.000')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_imessage_id = u'xxxxxx2015@icloud.com'
    self.assertEqual(event_object.imessage_id, expected_imessage_id)

    expected_read_receipt = 1
    self.assertEqual(event_object.read_receipt, expected_read_receipt)

    expected_message_type = 0
    self.assertEqual(event_object.message_type, expected_message_type)

    expected_attachment_location = None
    self.assertEqual(
        event_object.attachment_location, expected_attachment_location)

    expected_text = u'Did you try to send me a message?'
    self.assertEqual(event_object.text, expected_text)

    expected_msg = (
        u'iMessage ID: xxxxxx2015@icloud.com '
        u'Read Receipt: True '
        u'Message Type: Received '
        u'Service: iMessage '
        u'Message Content: Did you try to send me a message?')
    expected_short = u'Did you try to send me a message?'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
