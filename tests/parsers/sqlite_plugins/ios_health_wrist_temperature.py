#!/usr/bin/env python3
"""Tests for iOS Health Wrist Temperature SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_wrist_temperature

from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWristTemperatureTest(test_lib.SQLitePluginTestCase):
    """Tests for iOS Health Wrist Temperature SQLite database plugin."""

    def testProcess(self):
        """Test the plugin's Process function on a test database."""
        plugin = ios_health_wrist_temperature.IOSHealthWristTemperaturePlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["ios", "healthdb_secure_iOS_13_4_1.sqlite"], plugin
        )
        # 266 wrist temperature (sample) event data

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 266)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_recovery_warnings, 0)

        # Check wrist temperature (sample) event data.
        expected_event_values = {
            "added_time": "2020-04-16T15:06:51.871307+00:00",
            "algorithm_version": None,
            "data_type": "ios:health:wrist_temperature",
            "device_manufacturer": "Apple Inc.",
            "device_model": "Watch",
            "device_name": "Apple Watch",
            "end_time": "2020-04-16T16:00:00.000000+00:00",
            "hardware_version": "Watch4,3",
            "software_version": "6.2.1",
            "source": "This Iss Apple Watch",
            "start_time": "2020-04-16T15:00:00.000000+00:00",
            "surface_temperature_c": None,
            "surface_temperature_f": None,
            "wrist_temperature_c": None,
            "wrist_temperature_f": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
