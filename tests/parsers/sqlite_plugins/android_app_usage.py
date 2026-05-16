#!/usr/bin/env python3
"""Tests for the Android application usage database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_app_usage

from tests.parsers.sqlite_plugins import test_lib


class AndroidSQLiteAppUsagePluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the Android application usage database plugin."""

    def testProcess(self):
        """Test the Process function on an Android app_usage file."""
        plugin = android_app_usage.AndroidSQLiteAppUsage()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["android", "app_usage"], plugin
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 11545)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "android:sqlite:app_usage",
            "package_name": "com.whatsapp",
            "start_time": "2023-05-31T01:29:31.577+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 339)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
