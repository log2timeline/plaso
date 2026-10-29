#!/usr/bin/env python3
"""Tests for the Windows Event Log resources database reader."""

import unittest

from plaso.output import winevt_rc

from tests import test_lib as shared_test_lib


class WinevtResourcesHelperTest(shared_test_lib.BaseTestCase):
    """Tests for the Windows EventLog resources helper."""

    # pylint: disable=protected-access

    def testGetWinevtRcDatabaseMessageString(self):
        """Tests the _GetWinevtRcDatabaseMessageString function."""
        database_path = self._GetTestFilePath(["winevt-rc.db"])
        self._SkipIfPathNotExists(database_path)

        test_helper = winevt_rc.WinevtResourcesHelper(
            None, shared_test_lib.TEST_DATA_PATH, 0x00000409
        )
        message_string = test_helper._GetWinevtRcDatabaseMessageString(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            0xB00003ED,
            None,
        )
        expected_message_string = (
            "Your computer has detected that the IP address {0:s} for the Network "
            "Card with network address {2:s} is already in use on the network. "
            "Your computer will automatically attempt to obtain a different "
            "address."
        )
        self.assertEqual(message_string, expected_message_string)

    def testGetWinevtRcDatabaseParameterMessageString(self):
        """Tests the _GetWinevtRcDatabaseParameterMessageString function."""
        database_path = self._GetTestFilePath(["winevt-rc.db"])
        self._SkipIfPathNotExists(database_path)

        test_helper = winevt_rc.WinevtResourcesHelper(
            None, shared_test_lib.TEST_DATA_PATH, 0x00000409
        )
        message_string = test_helper._GetWinevtRcDatabaseParameterMessageString(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            0x00001712,
        )
        self.assertEqual(message_string, "No network adapters are available.")

    def testGetMessageString(self):
        """Tests the GetMessageString function."""
        database_path = self._GetTestFilePath(["winevt-rc.db"])
        self._SkipIfPathNotExists(database_path)

        test_helper = winevt_rc.WinevtResourcesHelper(
            None, shared_test_lib.TEST_DATA_PATH, 0x00000409
        )
        message_string = test_helper.GetMessageString(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            0xB00003ED,
            None,
        )
        self.assertIsNotNone(message_string)
        self.assertEqual(len(test_helper._missing_message_strings), 0)

        # Test that a lookup without a message string is cached.
        for _ in range(2):
            message_string = test_helper.GetMessageString(
                "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
                "Microsoft-Windows-Dhcp-Client",
                0xFFFFFFFF,
                None,
            )
            self.assertIsNone(message_string)

        self.assertEqual(len(test_helper._missing_message_strings), 1)

    def testGetParameterString(self):
        """Tests the GetParameterString function."""
        database_path = self._GetTestFilePath(["winevt-rc.db"])
        self._SkipIfPathNotExists(database_path)

        test_helper = winevt_rc.WinevtResourcesHelper(
            None, shared_test_lib.TEST_DATA_PATH, 0x00000409
        )
        message_string = test_helper.GetParameterString(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            0x00001712,
        )
        self.assertEqual(message_string, "No network adapters are available.")
        self.assertEqual(len(test_helper._missing_message_strings), 0)

        # Test that a lookup without a parameter string is cached.
        for _ in range(2):
            message_string = test_helper.GetParameterString(
                "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
                "Microsoft-Windows-Dhcp-Client",
                0xFFFFFFFF,
            )
            self.assertIsNone(message_string)

        self.assertEqual(len(test_helper._missing_message_strings), 1)

        # Test that a missing parameter string does not affect a message string
        # lookup with the same identifier.
        test_helper.GetMessageString(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            0xFFFFFFFF,
            None,
        )
        self.assertEqual(len(test_helper._missing_message_strings), 2)


if __name__ == "__main__":
    unittest.main()
