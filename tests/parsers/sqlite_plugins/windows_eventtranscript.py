# -*- coding: utf-8 -*-
"""Tests for the Windows Diagnosis EventTranscript database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import windows_eventtranscript

from tests.parsers.sqlite_plugins import test_lib


class EventTranscriptPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows Diagnosis EventTranscript database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = windows_eventtranscript.EventTranscriptPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['EventTranscript.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2526)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application_install_date': None,
        'application_name': None,
        'application_root_directory': None,
        'application_version': None,
        'compressed_payload_size': 50,
        'data_type': 'windows:diagnosis:eventtranscript',
        'event_keywords': 0x800000000000,
        'event_name_hash': 2681079708,
        'event_name': 'TelClientSyntheticScenario.AcceptingScenario_0',
        'friendly_logging_binary_name': '?unknown?',
        'ikey': 'o:0a89d516ae714e01ae89c96d185e9ae3',
        'is_core': 0,
        'logging_binary_name': '?unknown?',
        'name': 'TelClientSyntheticScenario.AcceptingScenario_0',
        'producer_identifier': 1,
        'provider_group_identifier': 1,
        'recorded_time': '2021-08-17T11:27:06.2573347+00:00',
        'user_identifier': None,
        'version': '4.0'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
