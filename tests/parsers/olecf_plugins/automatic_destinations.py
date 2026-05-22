#!/usr/bin/env python3
"""Tests for the .automaticDestinations-ms OLECF parser plugin."""

import unittest

from plaso.parsers.olecf_plugins import automatic_destinations

from tests.parsers.olecf_plugins import test_lib


class TestAutomaticDestinationsOLECFPlugin(test_lib.OLECFPluginTestCase):
    """Tests for the .automaticDestinations-ms OLECF parser plugin."""

    def testProcessVersion1(self):
        """Tests the Process function on version 1 .automaticDestinations-ms."""
        plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
        storage_writer = self._ParseOLECFFileWithPlugin(
            ["automaticDestinations-ms", "1b4dd67f29cb1962.automaticDestinations-ms"],
            plugin,
        )
        # Number of events:
        # olecf:dest_list:entry: 11
        # windows:lnk:link 33
        # windows:distributed_link_tracking:creation: 44

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 35)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Check a AutomaticDestinationsDestListEntryEvent.
        expected_event_values = {
            "birth_droid_file_identifier": "{9b1ce584-4a4c-11e5-b5c9-080027ac3d7f}",
            "birth_droid_volume_identifier": ("{fb6af886-05d7-402d-9741-d1ee9e64c41f}"),
            "data_type": "olecf:dest_list:entry",
            "droid_file_identifier": "{9b1ce584-4a4c-11e5-b5c9-080027ac3d7f}",
            "droid_volume_identifier": "{fb6af886-05d7-402d-9741-d1ee9e64c41f}",
            "entry_number": 7,
            "hostname": "student-pc1",
            "modification_time": "2015-08-29T15:32:44.0343008+00:00",
            "offset": 32,
            "path": "C:\\Users\\bperry\\Downloads",
            "pin_status": -1,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # Check a WinLnkLinkEvent.
        expected_event_values = {
            "access_time": "2015-08-25T10:30:31.7294695+00:00",
            "creation_time": "2015-08-25T10:30:26.4794695+00:00",
            "data_type": "windows:lnk:link",
            "drive_serial_number": 0x885029E6,
            "drive_type": 3,
            "file_attribute_flags": 0x00002020,
            "file_size": 3541,
            "link_target": "<Users Libraries> <Users property view>",
            "local_path": (
                "C:\\\\Users\\\\bperry\\\\AppData\\\\Roaming\\\\Microsoft\\\\"
                "Windows\\\\Libraries\\\\Documents.library-ms"
            ),
            "modification_time": "2015-08-25T10:30:31.7294695+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Check a WindowsDistributedLinkTrackingCreationEvent.
        expected_event_values = {
            "creation_time": "2015-08-24T10:40:58.5000324+00:00",
            "data_type": "windows:distributed_link_tracking:creation",
            "mac_address": "08:00:27:ac:3d:7f",
            "origin": "DestList entry at offset: 0x00000020",
            "uuid": "9b1ce584-4a4c-11e5-b5c9-080027ac3d7f",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessVersion3(self):
        """Tests the Process function on version 3 .automaticDestinations-ms."""
        plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
        storage_writer = self._ParseOLECFFileWithPlugin(
            ["automaticDestinations-ms", "9d1f905ce5044aee.automaticDestinations-ms"],
            plugin,
        )
        # Event data types:
        # olecf:dest_list:entry: 2
        # windows:lnk:link 2

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Check a AutomaticDestinationsDestListEntryEvent.
        expected_event_values = {
            "birth_droid_file_identifier": "{00000000-0000-0000-0000-000000000000}",
            "birth_droid_volume_identifier": ("{00000000-0000-0000-0000-000000000000}"),
            "data_type": "olecf:dest_list:entry",
            "droid_file_identifier": "{00000000-0000-0000-0000-000000000000}",
            "droid_volume_identifier": "{00000000-0000-0000-0000-000000000000}",
            "entry_number": 2,
            "hostname": None,
            "modification_time": "2016-01-17T13:08:08.2475045+00:00",
            "offset": 32,
            "path": "http://support.microsoft.com/kb/3124263",
            "pin_status": -1,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Check a WinLnkLinkEvent.
        expected_event_values = {
            "access_time": None,
            "creation_time": None,
            "data_type": "windows:lnk:link",
            "drive_serial_number": None,
            "drive_type": None,
            "file_attribute_flags": 0,
            "file_size": 0,
            "link_target": "<Internet Folder> <UNKNOWN: 0x61>",
            "local_path": None,
            "modification_time": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
