#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Kik messenger SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_kik

from tests.parsers.sqlite_plugins import test_lib


class IOSKikMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the iOS Kik messenger SQLite database plugin."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_kik.IOSKikPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['kik_ios.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 60)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'Hello',
        'data_type': 'ios:kik:messaging',
        'displayname': 'Ken Doh',
        'message_status': 94,
        'message_type': 2,
        'received_time': '2015-06-29T12:26:11.584833+00:00',
        'username': 'ken.doh'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
