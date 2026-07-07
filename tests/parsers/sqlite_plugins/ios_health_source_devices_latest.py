#!/usr/bin/env python3
"""Tests for iOS Health Source Devices Latest SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_source_devices_latest
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthSourceDevicesLatestTest(test_lib.SQLitePluginTestCase):
    """Tests for iOS Health Source Devices Latest SQLite database plugin."""

    def testProcess(self):
        """Test the Process function for source devices."""
        plugin = ios_health_source_devices_latest.IOSHealthSourceDevicesLatestPlugin()

        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_17.sqlite"], plugin
        )
        # 25 source device (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 25)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        expected_event_values = {
            "added_time": "2023-05-19T16:03:01.287088+00:00",
            "data_type": "ios:health:source_devices_latest",
            "device_name": "This Is’s AirPods",
            "firmware": None,
            "hardware": None,
            "local_identifier": "08:65:18:75:5E:75-tacl",
            "manufacturer": "Apple Inc.",
            "model": "0x2013",
            "software": None,
            "sync_identity": 1,
            "sync_provenance": 53,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
