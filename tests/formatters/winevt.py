#!/usr/bin/env python3
"""Tests for the Windows EventLog custom event formatter helpers."""

import unittest

from plaso.formatters import winevt

from tests.formatters import test_lib


class WindowsEventLogMessageFormatterHelperTest(test_lib.EventFormatterTestCase):
    """Tests for the Windows EventLog message formatter helper."""

    # pylint: disable=protected-access

    def testFormatStringValue(self):
        """Tests the _FormatStringValue function."""
        database_path = self._GetTestFilePath(["winevt-rc.db"])
        self._SkipIfPathNotExists(database_path)

        output_mediator = self._CreateOutputMediator()
        formatter_helper = winevt.WindowsEventLogMessageFormatterHelper()
        formatter_helper._winevt_resources_helper = (
            output_mediator.GetWinevtResourcesHelper()
        )
        string = formatter_helper._FormatStringValue(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            "%%5906",
        )
        self.assertEqual(string, "No network adapters are available.")

        string = formatter_helper._FormatStringValue(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            "%%640 %%641",
        )
        expected_string = (
            "ERROR_MULTIPLE_FAULT_VIOLATION The system is in the process of shutting "
            "down."
        )
        self.assertEqual(string, expected_string)

    def testFormatEventValues(self):
        """Tests the FormatEventValues function."""
        database_path = self._GetTestFilePath(["winevt-rc.db"])
        self._SkipIfPathNotExists(database_path)

        formatter_helper = winevt.WindowsEventLogMessageFormatterHelper()
        output_mediator = self._CreateOutputMediator()
        event_values = {
            "event_identifier": 1005,
            "event_version": 0,
            "message_identifier": 0xB00003ED,
            "provider_identifier": "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "source_name": "Microsoft-Windows-Dhcp-Client",
            "strings": ["192.168.1.15", "", "00-1A-2B-3C-4D-5E"]
        }
        formatter_helper.FormatEventValues(output_mediator, event_values)
        expected_string = (
            "Your computer has detected that the IP address 192.168.1.15 for the "
            "Network Card with network address 00-1A-2B-3C-4D-5E is already in use on "
            "the network. Your computer will automatically attempt to obtain a "
            "different address."
        )
        self.assertEqual(event_values["message_string"], expected_string)


if __name__ == "__main__":
    unittest.main()
