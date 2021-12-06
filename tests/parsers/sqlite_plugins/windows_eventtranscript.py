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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2526)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'application_install_date': None,
        'application_name': None,
        'application_root_directory': None,
        'application_version': None,
        'compressed_payload_size': 50,
        'data_type': 'windows:diagnosis:eventtranscript',
        'date_time': '2021-08-17 11:27:06.2573347',
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
        'user_identifier': None,
        'version': '4.0'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
