#!/usr/bin/env python3
"""Tests for the Windows Event Log resources database reader."""

import unittest

from plaso.output import winevt_rc

from tests import test_lib as shared_test_lib


class TestWinevtResourcesHelper(winevt_rc.WinevtResourcesHelper):
    """Windows EventLog resources helper with a small cache for testing."""

    _MAXIMUM_CACHED_MESSAGE_STRINGS = 2


class WinevtResourcesHelperTest(shared_test_lib.BaseTestCase):
    """Tests for the Windows EventLog resources helper."""

    # pylint: disable=protected-access

    _PROVIDER_IDENTIFIER = "{15a7a4f8-0072-4eab-abad-f98a4d666aed}"

    _LOG_SOURCE = "Microsoft-Windows-Dhcp-Client"

    def testCacheMessageString(self):
        """Tests the _CacheMessageString function."""
        test_helper = TestWinevtResourcesHelper(
            None, shared_test_lib.TEST_DATA_PATH, 0x00000409
        )

        test_helper._CacheMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 1, None, "test"
        )
        self.assertEqual(
            list(test_helper._message_string_cache.keys()),
            [(self._LOG_SOURCE, 1, None), (self._PROVIDER_IDENTIFIER, 1, None)],
        )

        # Test that an empty message string is not cached.
        test_helper._CacheMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 2, None, ""
        )
        self.assertEqual(len(test_helper._message_string_cache), 2)

        # Test that the least recently used lookup is removed.
        test_helper._CacheMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 3, None, None
        )
        self.assertEqual(
            list(test_helper._message_string_cache.keys()),
            [
                ("message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 3, None),
                (self._LOG_SOURCE, 1, None),
            ],
        )

    def testGetCachedMessageString(self):
        """Tests the _GetCachedMessageString function."""
        test_helper = winevt_rc.WinevtResourcesHelper(
            None, shared_test_lib.TEST_DATA_PATH, 0x00000409
        )

        lookup_result = test_helper._GetCachedMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 1, None
        )
        self.assertEqual(lookup_result, (False, None))

        test_helper._CacheMessageString(
            "message", self._PROVIDER_IDENTIFIER, None, 1, None, "test"
        )
        test_helper._CacheMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 2, None, None
        )

        lookup_result = test_helper._GetCachedMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 1, None
        )
        self.assertEqual(lookup_result, (True, "test"))

        lookup_result = test_helper._GetCachedMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 2, None
        )
        self.assertEqual(lookup_result, (True, None))

        # Test that a lookup without a message string is specific to the lookup
        # type and the combination of provider identifier and log source.
        lookup_result = test_helper._GetCachedMessageString(
            "parameter", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 2, None
        )
        self.assertEqual(lookup_result, (False, None))

        lookup_result = test_helper._GetCachedMessageString(
            "message", self._PROVIDER_IDENTIFIER, None, 2, None
        )
        self.assertEqual(lookup_result, (False, None))

        # Test that a lookup without a message string does not shadow a message
        # string cached for the provider identifier or log source.
        test_helper._CacheMessageString(
            "message", self._PROVIDER_IDENTIFIER, None, 2, None, "test"
        )

        lookup_result = test_helper._GetCachedMessageString(
            "message", self._PROVIDER_IDENTIFIER, self._LOG_SOURCE, 2, None
        )
        self.assertEqual(lookup_result, (True, "test"))

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
        self.assertEqual(len(test_helper._message_string_cache), 2)

        # Test that a lookup without a message string is cached.
        for _ in range(2):
            message_string = test_helper.GetMessageString(
                "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
                "Microsoft-Windows-Dhcp-Client",
                0xFFFFFFFF,
                None,
            )
            self.assertIsNone(message_string)

        self.assertEqual(len(test_helper._message_string_cache), 3)
        self.assertIn(
            (
                "message",
                "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
                "Microsoft-Windows-Dhcp-Client",
                0xFFFFFFFF,
                None,
            ),
            test_helper._message_string_cache,
        )

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
        self.assertEqual(len(test_helper._message_string_cache), 2)

        # Test that a lookup without a parameter string is cached.
        for _ in range(2):
            message_string = test_helper.GetParameterString(
                "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
                "Microsoft-Windows-Dhcp-Client",
                0xFFFFFFFF,
            )
            self.assertIsNone(message_string)

        self.assertEqual(len(test_helper._message_string_cache), 3)

        # Test that a missing parameter string does not affect a message string
        # lookup with the same identifier.
        test_helper.GetMessageString(
            "{15a7a4f8-0072-4eab-abad-f98a4d666aed}",
            "Microsoft-Windows-Dhcp-Client",
            0xFFFFFFFF,
            None,
        )
        self.assertEqual(len(test_helper._message_string_cache), 4)


if __name__ == "__main__":
    unittest.main()
