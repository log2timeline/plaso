#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the IMO HD Chat message database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_imohdchat

from tests.parsers.sqlite_plugins import test_lib


class IMOHDChatMessagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the IMO HD Chat message database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = ios_imohdchat.IMOHDChatMessagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['IMODb2.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 16)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'alias': 'This Is DFIR Two',
        'data_type': 'ios:imohdchat:message',
        'recorded_time': '2023-04-26T18:11:40.927000000+00:00',
        'status': 0,
        'text': 'Are you on imo?'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
