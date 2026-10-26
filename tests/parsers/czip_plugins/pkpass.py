#!/usr/bin/env python3
"""Tests for the Apple Wallet pass (pkpass) plugin."""

import io
import json
import unittest
import zipfile

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers.czip_plugins import pkpass

from tests.parsers.czip_plugins import test_lib


class AppleWalletPassPluginTest(test_lib.CompoundZIPPluginTestCase):
    """Tests for the Apple Wallet pass (pkpass) plugin."""

    def _ProcessPassJSON(self, pass_json_data):
        """Processes pass.json data with the plugin.

        Args:
          pass_json_data (bytes): contents of pass.json.

        Returns:
          FakeStorageWriter: storage writer.
        """
        parser_mediator = parsers_mediator.ParserMediator()

        storage_writer = self._CreateStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)
        parser_mediator.AppendToParserChain("czip")

        file_object = io.BytesIO()
        with zipfile.ZipFile(file_object, "w") as zip_file:
            zip_file.writestr("manifest.json", b"{}")
            zip_file.writestr("pass.json", pass_json_data)

        plugin = pkpass.AppleWalletPassPlugin()

        with zipfile.ZipFile(file_object, "r") as zip_file:
            plugin.UpdateChainAndProcess(parser_mediator, zip_file=zip_file)

        return storage_writer

    def testCheckRequiredPaths(self):
        """Tests the CheckRequiredPaths function."""
        plugin = pkpass.AppleWalletPassPlugin()

        for path_segments, expected_result in (
            (["wallet.pkpass"], True),
            (["Document.docx"], False),
            (["syslog.zip"], False),
        ):
            file_entry = self._GetTestFileEntry(path_segments)
            file_object = file_entry.GetFileObject()

            with zipfile.ZipFile(file_object, "r") as zip_file:
                result = plugin.CheckRequiredPaths(zip_file)

            self.assertEqual(result, expected_result)

    def testProcess(self):
        """Tests the Process function."""
        plugin = pkpass.AppleWalletPassPlugin()
        storage_writer = self._ParseZIPFileWithPlugin(["wallet.pkpass"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "apple:wallet:pass",
            "description": "Concert ticket",
            "expiration_time": "2025-06-15T02:00:00+00:00",
            "logo_text": "Example Concert Hall",
            "organization_name": "Example Concert Hall",
            "pass_type_identifier": "pass.org.example.event-ticket",
            "relevant_time": "2025-06-14T19:30:00-07:00",
            "serial_number": "TICKET-0001",
            "team_identifier": "A1B2C3D4E5",
            "voided": False,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithNotAPass(self):
        """Tests the Process function with a pass.json that is not a pass."""
        plugin = pkpass.AppleWalletPassPlugin()
        storage_writer = self._ParseZIPFileWithPlugin(
            ["wallet_not_a_pass.pkpass"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

    def testProcessWithInvalidValues(self):
        """Tests the Process function with invalid pass.json values."""
        pass_json = {
            "description": 1,
            "expirationDate": 1,
            "formatVersion": 1,
            "passTypeIdentifier": "pass.org.example.event-ticket",
            "relevantDate": "bogus",
            "serialNumber": "TICKET-0001",
        }
        storage_writer = self._ProcessPassJSON(json.dumps(pass_json).encode("utf-8"))

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 2)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertIsNone(event_data.description)
        self.assertIsNone(event_data.expiration_time)
        self.assertIsNone(event_data.relevant_time)

    def testProcessWithoutDates(self):
        """Tests the Process function with a pass.json without dates."""
        pass_json = {
            "formatVersion": 1,
            "passTypeIdentifier": "pass.org.example.event-ticket",
            "serialNumber": "TICKET-0001",
        }
        storage_writer = self._ProcessPassJSON(json.dumps(pass_json).encode("utf-8"))

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testProcessWithInvalidJSON(self):
        """Tests the Process function with a pass.json that is not JSON."""
        storage_writer = self._ProcessPassJSON(b"\xff not json")

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)


if __name__ == "__main__":
    unittest.main()
