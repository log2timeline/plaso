#!/usr/bin/env python3
"""Tests for iOS Health Source Devices SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_source_devices
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthSourceDevicesTest(test_lib.SQLitePluginTestCase):
    """Tests for iOS Health Source Devices SQLite database plugin."""

    def testProcess(self):
        """Test the Process function for source devices."""
        plugin = ios_health_source_devices.IOSHealthSourceDevicesPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )
        # 6 source device event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check source device event data.
        expected_event_values = {
            "added_time": "2020-03-21T22:33:20.752679+00:00",
            "device_name": "iPhone",
            "firmware": None,
            "hardware": "iPhone8,4",
            "local_identifier": None,
            "manufacturer": "Apple Inc.",
            "model": "iPhone",
            "software": "13.3.1",
            "sync_provenance": 0,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
