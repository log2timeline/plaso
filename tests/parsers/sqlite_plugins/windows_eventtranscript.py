# -*- coding: utf-8 -*-
"""Tests for the Windows diagnosis EventTranscript database plugin."""

import unittest

#pylint: disable=line-too-long, C0301
from plaso.parsers.sqlite_plugins import windows_eventtranscript as eventtranscript

from tests.parsers.sqlite_plugins import test_lib


class EventTranscriptPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows diagnosis EventTranscript database plugin."""

  def testProcess(self):
    """Tests the Process function on a Windows diagnosis EventTranscript
    database file.
    """
    plugin = eventtranscript.EventTranscriptPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['EventTranscript.db'], plugin)

    self.assertEqual(storage_writer.number_of_events, 4595)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the first page visited event.
    expected_event_values = {
        'data_type': 'windows:diagnosis:eventtranscript',
        'date_time': '2021-08-17 11:27:06.2573347',
        'sid': '',
        # pylint: disable=line-too-long
        'raw_payload': '{"ver":"4.0","name":"TelClientSyntheticScenario.AcceptingScenario_0","time":"2021-08-17T11:27:06.2573347Z","iKey":"o:0a89d516ae714e01ae89c96d185e9ae3","ext":{"utc":{"eventFlags":257,"pgName":"WIN","flags":469762632,"epoch":"1000837","seq":217},"metadata":{"privTags":16777216,"f":{"ScenarioId":8}},"os":{"bootId":10,"name":"Windows","ver":"10.0.19041.1165.amd64fre.vb_release.191206-1406"},"app":{"asId":63},"device":{"localId":"s:5A2CD9B2-5E46-4396-99A8-5C79DF95E368","deviceClass":"Windows.Desktop"},"protocol":{"devMake":"innotek GmbH","devModel":"VirtualBox"},"loc":{"tz":"+10:00"}},"data":{"ScenarioId":"7E9FEC95-51F6-482B-9D9E-7507E2B17F07","ScenarioName":"RDP Diagnostics Start Desktop OD V8"}}',
        'full_event_name': 'TelClientSyntheticScenario.AcceptingScenario_0',
        'full_event_name_hash': 2681079708,
        'event_keywords': 140737488355328,
        'is_core': 0,
        'provider_group_id': 1,
        'logging_binary_name': '?unknown?',
        'friendly_logging_binary_name': '?unknown?',
        'compressed_payload_size': 50,
        'producer_id': 1,
        'producer_id_text': 'Windows',
        'tag_id': 24,
        'locale_name': 'en-US',
        'tag_name': 'Product and Service Performance',
        'description': 'Data collected about the measurement, performance and operation of the capabilities of the product or service.  This data represents information about the capability and its use, with a focus on providing the capabilities of the product or service.',
        'ver': '4.0',
        'name': 'TelClientSyntheticScenario.AcceptingScenario_0',
        'time': '2021-08-17T11:27:06.2573347Z',
        'ikey': 'o:0a89d516ae714e01ae89c96d185e9ae3',
        'ext': '{"utc":{"eventFlags":257,"pgName":"WIN","flags":469762632,"epoch":"1000837","seq":217},"metadata":{"privTags":16777216,"f":{"ScenarioId":8}},"os":{"bootId":10,"name":"Windows","ver":"10.0.19041.1165.amd64fre.vb_release.191206-1406"},"app":{"asId":63},"device":{"localId":"s:5A2CD9B2-5E46-4396-99A8-5C79DF95E368","deviceClass":"Windows.Desktop"},"protocol":{"devMake":"innotek GmbH","devModel":"VirtualBox"},"loc":{"tz":"+10:00"}}',
        'data': '{"ScenarioId":"7E9FEC95-51F6-482B-9D9E-7507E2B17F07","ScenarioName":"RDP Diagnostics Start Desktop OD V8"}',
        }

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
