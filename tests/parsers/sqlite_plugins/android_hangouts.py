#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Hangouts messages plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_hangouts

from tests.parsers.sqlite_plugins import test_lib


class AndroidHangoutsMessagesTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Hangouts message database plugin."""

  def testProcess(self):
    """Test the Process function on a Google hangouts file."""
    plugin = android_hangouts.AndroidHangoutsMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['googlehangouts.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'How are you?',
        'creation_time': '2017-07-17T04:41:54.326967+00:00',
        'data_type': 'android:messaging:hangouts',
        'message_status': 4,
        'message_type': 2,
        'sender': 'John Macron'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
