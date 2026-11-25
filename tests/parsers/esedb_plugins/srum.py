#!/usr/bin/env python3
"""Tests for the System Resource Usage Monitor (SRUM) ESE database file."""

import unittest

from plaso.parsers.esedb_plugins import srum

from tests.parsers.esedb_plugins import test_lib


class SystemResourceUsageMonitorESEDBPluginTest(test_lib.ESEDBPluginTestCase):
    """Tests for the System Resource Usage Monitor (SRUM) ESE database plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plugin = srum.SystemResourceUsageMonitorESEDBPlugin()
        storage_writer = self._ParseESEDBFileWithPlugin(["SRUDB.dat"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 18318)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test an entry with data type windows:srum:application_usage
        expected_event_values = {
            "application": "Memory Compression",
            "data_type": "windows:srum:application_usage",
            "identifier": 22167,
            "recorded_time": "2017-11-05T11:32:00.000000+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1913)
        self.CheckEventData(event_data, expected_event_values)

        # Test an entry with data type windows:srum:network_connectivity
        expected_event_values = {
            "application": 1,
            "data_type": "windows:srum:network_connectivity",
            "identifier": 501,
            "last_connected_time": "2017-11-05T10:30:48.1679714+00:00",
            "recorded_time": "2017-11-05T13:33:00.000000+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 18062)
        self.CheckEventData(event_data, expected_event_values)

        # Test an entry with data type windows:srum:push_notification
        expected_event_values = {
            "application": (
                "Microsoft.Office.OneNote_17.7668.58071.0_x64__8wekyb3d8bbwe"
            ),
            "data_type": "windows:srum:push_notification",
            "identifier": 1,
            "network_type": 0,
            "notification_type": 1,
            "payload_size": 2196,
            "recorded_time": "2017-07-30T10:46:00.000000+00:00",
            "user_identifier": "S-1-5-21-1670443002-3598886608-1280426916-1001",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1840)
        self.CheckEventData(event_data, expected_event_values)

        # Test an entry with data type windows:srum:network_usage
        expected_event_values = {
            "application": "DiagTrack",
            "bytes_sent": 2076,
            "data_type": "windows:srum:network_usage",
            "identifier": 3495,
            "interface_luid": 1689399632855040,
            "recorded_time": "2017-11-05T11:32:00.000000+00:00",
            "user_identifier": "S-1-5-18",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
