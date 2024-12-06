# -- coding: utf-8 --
"""Tests for the SQLite parser plugin for Android
communication information database files."""

import unittest

from plaso.parsers.sqlite_plugins import android_communication_information

from tests.parsers.sqlite_plugins import test_lib


class AndroidCommunicationInformationPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite parser plugin for Android communication information
  database files."""

  def testParse(self):
    """Tests the ParseCommunicationInformationRow method."""
    plugin = (
      android_communication_information.AndroidCommunicationInformationPlugin()
    )
    storage_writer = self._ParseDatabaseFileWithPlugin(['burners.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
      'event_data')
    self.assertEqual(number_of_event_data, 25)
    # Adjust the number based on the test dataset.

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
      'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
      'phone_number_id': '123456789',
      'voicemail_url': 'http://voicemail.url/sample',
      'user_id': 'user_01',
      'name': 'Sample Burner',
      'alias': 'Alias Burner',
      'features': 'Call, Text',
      'total_minutes': 500,
      'expiration_date': '2024-01-15T12:34:56+00:00',# Adjust to your dataset.
      'date_created': '2023-01-15T12:34:56+00:00', # Adjust to your dataset.
      'last_updated_date': '2023-12-01T12:34:56+00:00',
      # Adjust to your dataset.
      'renewal_date': '2024-01-01T00:00:00+00:00' # Adjust to your dataset.
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    # Adjust the index based on expected records.
    self.CheckEventData(event_data, expected_event_values)


if _name_ == '_main_':
  unittest.main()
