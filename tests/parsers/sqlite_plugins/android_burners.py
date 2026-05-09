#!/usr/bin/env python3
"""Tests for the Android Burner plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_burners

from tests.parsers.sqlite_plugins import test_lib


class AndroidBurnerPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Burner database plugin."""

  def testProcess(self):
    """Test the Process function on an Android burners.db file."""
    plugin = android_burners.AndroidBurnerPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin([
        'burners.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'alias': None,
        'creation_time': '2022-12-01T17:19:27.768+00:00',
        'expiration_time': '2022-12-31T17:19:27.768+00:00',
        'last_updated_time': '2022-12-01T17:19:27.768+00:00',
        'name': 'My Burner',
        'phone_number': '+19102484781',
        'total_minutes': 50,
        'user_identifier': '21d2ca9c-aba1-4ada-b7f5-23b0d97acb47',
        'voicemail_url': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
