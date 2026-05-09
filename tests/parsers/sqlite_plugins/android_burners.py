# -- coding: utf-8 --
"""Tests for the Android Burners App plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_burners

from tests.parsers.sqlite_plugins import test_lib


class AndroidCommunicationInformationPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Burners App database plugin."""

  def testParse(self):
    """Test the Process function on an Android burners.db file."""
    plugin = android_burners.AndroidCommunicationInformationPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['burners.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'alias': 'Alias Burner',
        'date_created': '2023-01-15T12:34:56+00:00',
        'expiration_date': '2024-01-15T12:34:56+00:00',
        'features': 'Call, Text',
        'last_updated_date': '2023-12-01T12:34:56+00:00',
        'name': 'Sample Burner',
        'phone_number_id': '123456789',
        'renewal_date': '2024-01-01T00:00:00+00:00',
        'total_minutes': 500,
        'user_id': 'user_01',
        'voicemail_url': 'http://voicemail.url/sample'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '_main_':
  unittest.main()
