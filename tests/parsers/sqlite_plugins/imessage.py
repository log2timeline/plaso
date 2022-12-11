#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iMessage plugin."""

import unittest

from plaso.parsers.sqlite_plugins import imessage

from tests.parsers.sqlite_plugins import test_lib


class IMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the iMessage database plugin."""

  def testProcess(self):
    """Test the Process function on a iMessage chat.db file."""
    plugin = imessage.IMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['imessage_chat.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2015-11-30T10:48:40.000000+00:00',
        'data_type': 'imessage:event:chat',
        'imessage_id': 'xxxxxx2015@icloud.com',
        'message_type': 0,
        'read_receipt': 1,
        'service': 'iMessage',
        'text': 'Did you try to send me a message?'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
