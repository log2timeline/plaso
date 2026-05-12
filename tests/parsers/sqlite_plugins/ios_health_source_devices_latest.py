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
            "creation_date_str": "2020-03-21 20:28:48.950322",
            "data_type": "ios:health:source_devices_latest",
            "device_name": "Apple Watch",
            "firmware": None,
            "hardware": "Watch4,3",
            "local_identifier": None,
            "manufacturer": "Apple Inc.",
            "model": "Watch",
            "software": "6.1.3",
            "sync_identity": 1,
            "sync_provenance": 47,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
