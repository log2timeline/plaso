#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for TikTok on iOS SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_tiktok_contacts

from tests.parsers.sqlite_plugins import test_lib


class IOSTikTokContactsTest(test_lib.SQLitePluginTestCase):
  """Tests for TikTok on iOS SQLite database plugin."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_tiktok_contacts.IOSTikTokContactsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['AwemeIM.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_recovery_warnings = (
        storage_writer.GetNumberOfAttributeContainers('recovery_warning'))
    self.assertEqual(number_of_recovery_warnings, 0)

        # Test a TikTok contact database entry.
    expected_event_values = {
        'chat_timestamp': '2021-12-03T00:00:00+00:00',
        'data_type': 'ios:tiktok:contact',
        'nickname': 'sample_user',
        'url': 'https://www.tiktok.com/@sample_user'
    }

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
