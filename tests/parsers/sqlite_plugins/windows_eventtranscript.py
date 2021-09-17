# -*- coding: utf-8 -*-
"""Tests for the Windows Diagnosis EventTranscript database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import windows_eventtranscript

from tests.parsers.sqlite_plugins import test_lib


class EventTranscriptPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows Diagnosis EventTranscript database plugin."""

  def testProcess(self):
    """Tests the Process function on a Windows Diagnosis EventTranscript
    database file.
    """
    plugin = windows_eventtranscript.EventTranscriptPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['EventTranscript.db'], plugin)

    self.assertEqual(storage_writer.number_of_events, 2526)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the first record in the events_persisted table.
    expected_event_values = {
        'data_type': 'windows:diagnosis:eventtranscript',
        'date_time': '2021-08-17 11:27:06.2573347',
        'sid': '',
        'raw_payload': (
            '{"ver":"4.0","name":"TelClientSyntheticScenario.AcceptingScenar'
            'io_0","time":"2021-08-17T11:27:06.2573347Z","iKey":"o:0a89d516ae'
            '714e01ae89c96d185e9ae3","ext":{"utc":{"eventFlags":257,"pgName":'
            '"WIN","flags":469762632,"epoch":"1000837","seq":217},"metadata":'
            '{"privTags":16777216,"f":{"ScenarioId":8}},"os":{"bootId":10,"na'
            'me":"Windows","ver":"10.0.19041.1165.amd64fre.vb_release.191206-'
            '1406"},"app":{"asId":63},"device":{"localId":"s:5A2CD9B2-5E46-43'
            '96-99A8-5C79DF95E368","deviceClass":"Windows.Desktop"},"protocol'
            '":{"devMake":"innotek GmbH","devModel":"VirtualBox"},"loc":{"tz"'
            ':"+10:00"}},"data":{"ScenarioId":"7E9FEC95-51F6-482B-9D9E-7507E2'
            'B17F07","ScenarioName":"RDP Diagnostics Start Desktop OD V8"}}'),
        'full_event_name': 'TelClientSyntheticScenario.AcceptingScenario_0',
        'full_event_name_hash': 2681079708,
        'event_keywords': 140737488355328,
        'is_core': 0,
        'provider_group_id': 1,
        'logging_binary_name': '?unknown?',
        'friendly_logging_binary_name': '?unknown?',
        'compressed_payload_size': 50,
        'producer_id': 1,
        'ver': '4.0',
        'name': 'TelClientSyntheticScenario.AcceptingScenario_0',
        'time': '2021-08-17T11:27:06.2573347Z',
        'ikey': 'o:0a89d516ae714e01ae89c96d185e9ae3',
        'ext': (
            '{"utc":{"eventFlags":257,"pgName":"WIN","flags":469'
            '762632,"epoch":"1000837","seq":217},"metadata":{"privTags":16777'
            '216,"f":{"ScenarioId":8}},"os":{"bootId":10,"name":"Windows","ve'
            'r":"10.0.19041.1165.amd64fre.vb_release.191206-1406"},"app":{"as'
            'Id":63},"device":{"localId":"s:5A2CD9B2-5E46-4396-99A8-5C79DF95E'
            '368","deviceClass":"Windows.Desktop"},"protocol":{"devMake":"inn'
            'otek GmbH","devModel":"VirtualBox"},"loc":{"tz":"+10:00"}}'),
        'data': (
            '{"ScenarioId":"7E9FEC95-51F6-482B-9D9E-7507E2B17F07","ScenarioNa'
            'me":"RDP Diagnostics Start Desktop OD V8"}'),
        'app_name': None,
        'app_version': None,
        'app_root_dir_path': None,
        'app_install_date': None,
        }

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
