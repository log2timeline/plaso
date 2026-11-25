#!/usr/bin/env python3
"""Tests for the Windows Update datastore ESE database file."""

import unittest

from plaso.parsers.esedb_plugins import windows_update_datastore

from tests.parsers.esedb_plugins import test_lib


class WindowsUpdateDatastoreESEDBPluginTest(test_lib.ESEDBPluginTestCase):
    """Tests for the Windows Update datastore ESE database plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plugin = windows_update_datastore.WindowsUpdateDatastoreESEDBPlugin()
        storage_writer = self._ParseESEDBFileWithPlugin(
            ["windows_update_datastore.edb"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test tbFiles table event data.
        expected_event_values = {
            "data_type": "windows:update_datastore:file",
            "digest": "0da81c5bc3ca1c425f383eb8b713d4949f11a9c6",
            "digest_algorithm": "SHA1",
            "file_size": 96721052,
            "identifier": 3,
            "modification_time": "2026-10-10T01:03:43.3067203+00:00",
            "name": "Windows11.0-KB5127690-x64-NDP481.cab",
            "server_identifier": "{f63faf79-b4aa-4d54-a4fc-a361fa63eb4a}",
            "strong_digest": (
                "df471a4afb67951bb63997096995e87c91bbf1c8167424b90569af8401c283a0"
            ),
            "strong_digest_algorithm": "SHA256",
            "url": "http://www.windowsupdate.com/Windows11.0-KB5127690-x64-NDP481.cab",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Test tbHistory table event data.
        expected_event_values = {
            "categories": "Windows",
            "classification": "{0fa1201d-4330-4fa8-8ae9-b877473b6441}",
            "client_identifier": "wusa",
            "data_type": "windows:update_datastore:history",
            "description": "Fix for KB5127690",
            "identifier": 1,
            "mapped_result_code": 0x80242014,
            "more_information_url": "http://support.microsoft.com/?kbid=5127690",
            "recorded_time": "2026-11-16T00:54:00.000000+00:00",
            "revision_number": 501,
            "server_identifier": "{f63faf79-b4aa-4d54-a4fc-a361fa63eb4a}",
            "server_selection": 4,
            "status": 1,
            "support_url": "http://support.microsoft.com",
            "title": "Update for Windows (KB5127690)",
            "unmapped_result_code": 0,
            "update_identifier": "{f4c6c5be-4c30-4957-b9b6-b0e8de5f80e8}",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        # Test tbUpdates table event data.
        expected_event_values = {
            "data_type": "windows:update_datastore:update",
            "identifier": 413,
            "kb_article_identifiers": None,
            "more_information_url": None,
            "msrc_severity": None,
            "product_name": None,
            "revision_number": 501,
            "server_identifier": None,
            "support_url": None,
            "update_identifier": "{ab772742-e2ae-46a3-bc45-8e36b6592729}",
            "update_type": 2,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
