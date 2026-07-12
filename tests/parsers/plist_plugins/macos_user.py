#!/usr/bin/env python3
"""Tests for the MacOS local users plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macos_user

from tests.parsers.plist_plugins import test_lib


class MacOSUserPlistPluginTest(test_lib.PlistPluginTestCase):
    """Tests for the MacOS local user plist plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plist_name = "user.plist"

        plugin = macos_user.MacOSUserPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, ["plist", plist_name], plist_name
        )
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
            "data_type": "macos:user:entry",
            "fullname": "Joaquin Moreno",
            "last_login_attempt_time": None,
            "last_login_time": None,
            "last_password_set_time": "2013-12-28T04:35:47+00:00",
            "password_hash": (
                "$ml$37313$fa6cac1869263baa85cffc5e77a3d4ee164b75536cae26ce8547108f60e"
                "3f554$a731dbb0e386b169af89fbb33c255ceafc083c6bc5194853f72f11c550c42e4"
                "625ef113b66f3f8b51fc3cd39106bad5067db3f7f1491758ffe0d819a1b0aba20646f"
                "d61345d98c0c9a411bfd1144dd4b3c40ec0f148b66d5b9ab014449f9b2e103928ef21"
                "db6e25b536a60ff17a84e985be3aa7ba3a4c16b34e0d1d2066ae178"
            ),
            "user_identifier": "501",
            "username": "user",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
