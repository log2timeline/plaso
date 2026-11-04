#!/usr/bin/env python3
"""Tests for the formatters configuration files."""

import glob
import os
import unittest

from plaso.formatters import interface
from plaso.formatters import yaml_formatters_file

from tests import test_lib as shared_test_lib


class FormattersDataTest(shared_test_lib.BaseTestCase):
    """Tests the formatters configuration files."""

    def _GetFormattersPerDataType(self, path):
        """Retrieves the formatters per data type defined in a file.

        Args:
          path (str): path of the formatters file.

        Returns:
          dict[str, EventFormatter]: formatters per data type.
        """
        formatters_file = yaml_formatters_file.YAMLFormattersFile()
        return {
            formatter.data_type: formatter
            for formatter in formatters_file.ReadFromFile(path)
        }

    def testConditionalFormatStringPieces(self):
        """Tests that conditional format string pieces contain 1 attribute name."""
        formatters_directory_path = self._GetDataFilePath(["formatters"])
        self._SkipIfPathNotExists(formatters_directory_path)

        formatters_file = yaml_formatters_file.YAMLFormattersFile()

        paths = sorted(glob.glob(os.path.join(formatters_directory_path, "*.yaml")))
        self.assertNotEqual(paths, [])

        issues = []
        for path in paths:
            filename = os.path.basename(path)
            for formatter in formatters_file.ReadFromFile(path):
                if not isinstance(formatter, interface.ConditionalEventFormatter):
                    continue

                try:
                    # Creating the message builds and validates the format
                    # string pieces maps.
                    formatter.GetMessage({})
                except RuntimeError as exception:
                    issues.append(
                        f"{filename:s}: {formatter.data_type:s}: {exception!s}"
                    )

        self.assertEqual(issues, [])

    def testIOSHealthMessages(self):
        """Tests the iOS Health messages."""
        formatters_file_path = self._GetDataFilePath(["formatters", "ios.yaml"])
        self._SkipIfPathNotExists(formatters_file_path)

        formatters = self._GetFormattersPerDataType(formatters_file_path)

        formatter = formatters["ios:health:heart_rate"]

        event_values = {
            "bpm": 73,
            "context": 1.0,
            "device_name": "Apple Watch",
            "hardware": "Watch4,3",
            "software_version": "6.1.3",
            "source_name": "This Is’s Apple Watch",
            "time_zone": "America/New_York",
        }
        formatter.FormatEventValues(None, event_values)

        expected_message = (
            "Heart Rate: 73 BPM Context: Background Device: Apple Watch (Watch4,3) "
            "Source: This Is’s Apple Watch (v6.1.3) Time Zone: America/New_York"
        )
        self.assertEqual(formatter.GetMessage(event_values), expected_message)
        self.assertEqual(formatter.GetMessageShort(event_values), "73 BPM (1.0)")

        event_values = {
            "bpm": 73,
            "context": None,
            "device_name": "Apple Watch",
            "hardware": None,
            "software_version": None,
            "source_name": "This Is’s Apple Watch",
            "time_zone": None,
        }
        formatter.FormatEventValues(None, event_values)

        expected_message = (
            "Heart Rate: 73 BPM Device: Apple Watch Source: This Is’s Apple Watch"
        )
        self.assertEqual(formatter.GetMessage(event_values), expected_message)
        self.assertEqual(formatter.GetMessageShort(event_values), "73 BPM")

        formatter = formatters["ios:health:source_devices"]

        event_values = {
            "device_name": "iPhone",
            "firmware": None,
            "hardware": "iPhone8,4",
            "local_identifier": None,
            "manufacturer": "Apple Inc.",
            "model": "iPhone",
            "software": "13.3.1",
            "synchronization_provenance": 0,
        }

        expected_message = (
            "Device Name: iPhone Manufacturer: Apple Inc. Model: iPhone "
            "Hardware Version: iPhone8,4 Software/Firmware: 13.3.1 "
            "Synchronization Provenance: 0"
        )
        self.assertEqual(formatter.GetMessage(event_values), expected_message)
        self.assertEqual(
            formatter.GetMessageShort(event_values), "Source Device: iPhone (iPhone)"
        )

        event_values["firmware"] = "1.0"

        expected_message = (
            "Device Name: iPhone Manufacturer: Apple Inc. Model: iPhone "
            "Hardware Version: iPhone8,4 Software/Firmware: 13.3.1 / 1.0 "
            "Synchronization Provenance: 0"
        )
        self.assertEqual(formatter.GetMessage(event_values), expected_message)


if __name__ == "__main__":
    unittest.main()
