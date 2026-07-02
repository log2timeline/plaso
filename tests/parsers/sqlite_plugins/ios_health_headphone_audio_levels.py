#!/usr/bin/env python3
"""Tests for iOS Health Headphone Audio Levels SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_headphone_audio_levels
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthHeadphoneAudioPluginGoldenTest(test_lib.SQLitePluginTestCase):
    """Golden-value tests for the iOS Health Headphone Audio Levels plugin."""

    def testProcess(self):
        """Tests the Process function on a healthdb_secure.sqlite file."""
        plugin = ios_health_headphone_audio_levels.IOSHealthHeadphoneAudioPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )
        # 8 headphone audio level (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check headphone audio level (sample) event data.
        expected_event_values = {
            "bundle_name": "com.apple.Music",
            "data_id": 15025,
            "data_type": "ios:health:headphone_audio_levels",
            "decibels": 70.3830005252994,
            "device_manufacturer": "Apple Inc.",
            "device_model": "0x2002",
            "device_name": "AirPods",
            "end_time": "2020-03-27T19:19:09.039616+00:00",
            "local_identifier": "7C:04:D0:89:89:A0-tacl",
            "start_time": "2020-03-27T18:55:14.121677+00:00",
            "total_time_duration": "00:23:54",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
