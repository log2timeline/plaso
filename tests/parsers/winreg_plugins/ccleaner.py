#!/usr/bin/env python3
"""Tests for the CCleaner Windows Registry plugin."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import ccleaner

from tests.parsers.winreg_plugins import test_lib


class CCleanerRegistryPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the CCleaner Windows Registry plugin."""

    # pylint: disable=protected-access

    def testParseUpdateKeyValue(self):
        """Tests the _ParseUpdateKeyValue function."""
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        plugin = ccleaner.CCleanerPlugin()

        test_cases = [
            ("07/13/2013 12:03:14 AM", "2013-07-13 00:03:14"),
            ("07/13/2013 12:03:14 PM", "2013-07-13 12:03:14"),
            ("07/13/2013 01:03:14 PM", "2013-07-13 13:03:14"),
        ]
        for value_string, expected_date_time_string in test_cases:
            registry_value = dfwinreg_fake.FakeWinRegistryValue(
                "UpdateKey",
                data=value_string.encode("utf_16_le"),
                data_type=dfwinreg_definitions.REG_SZ,
            )
            date_time = plugin._ParseUpdateKeyValue(parser_mediator, registry_value)
            self.assertIsNotNone(date_time)
            self.assertEqual(
                date_time.CopyToDateTimeString(), expected_date_time_string
            )

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        for value_string in ("07/13/2013 00:03:14 AM", "07/13/2013 13:03:14 PM"):
            storage_writer = self._CreateStorageWriter()
            parser_mediator = self._CreateParserMediator(storage_writer)

            registry_value = dfwinreg_fake.FakeWinRegistryValue(
                "UpdateKey",
                data=value_string.encode("utf_16_le"),
                data_type=dfwinreg_definitions.REG_SZ,
            )
            date_time = plugin._ParseUpdateKeyValue(parser_mediator, registry_value)
            self.assertIsNone(date_time)

            number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
                "extraction_warning"
            )
            self.assertEqual(number_of_warnings, 1)

    # pylint: disable=protected-access

    def testParseUpdateKeyValue(self):
        """Tests the _ParseUpdateKeyValue function."""
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        plugin = ccleaner.CCleanerPlugin()

        test_cases = [
            ("07/13/2013 10:03:14 AM", "2013-07-13 10:03:14"),
            ("07/13/2013 01:03:14 PM", "2013-07-13 13:03:14"),
        ]
        for value_string, expected_date_time_string in test_cases:
            registry_value = dfwinreg_fake.FakeWinRegistryValue(
                "UpdateKey",
                data=value_string.encode("utf_16_le"),
                data_type=dfwinreg_definitions.REG_SZ,
            )
            date_time = plugin._ParseUpdateKeyValue(parser_mediator, registry_value)
            self.assertIsNotNone(date_time)
            self.assertTrue(date_time.is_local_time)
            self.assertEqual(
                date_time.CopyToDateTimeString(), expected_date_time_string
            )

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        test_cases = [
            (
                b"\x01\x00\x00\x00",
                dfwinreg_definitions.REG_DWORD,
                "unsupported UpdateKey value data type: REG_DWORD_LE",
            ),
            (b"", dfwinreg_definitions.REG_SZ, "missing UpdateKey value data"),
            (
                "2013-07-13 10:03:14".encode("utf_16_le"),
                dfwinreg_definitions.REG_SZ,
                "unsupported UpdateKey value data: 2013-07-13 10:03:14",
            ),
            (
                "13/45/2013 10:03:14 AM".encode("utf_16_le"),
                dfwinreg_definitions.REG_SZ,
                "invalid UpdateKey date time value: (2013, 13, 45, 10, 3, 14)",
            ),
        ]
        for value_data, data_type, expected_warning_message in test_cases:
            storage_writer = self._CreateStorageWriter()
            parser_mediator = self._CreateParserMediator(storage_writer)

            registry_value = dfwinreg_fake.FakeWinRegistryValue(
                "UpdateKey", data=value_data, data_type=data_type
            )
            date_time = plugin._ParseUpdateKeyValue(parser_mediator, registry_value)
            self.assertIsNone(date_time)

            warning_messages = [
                warning.message
                for warning in storage_writer.GetAttributeContainers(
                    "extraction_warning"
                )
            ]
            self.assertEqual(warning_messages, [expected_warning_message])

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = ccleaner.CCleanerPlugin()

        self._AssertFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER\\Software", "Piriform\\CCleaner"
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE\\Software", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        test_file_entry = self._GetTestFileEntry(["NTUSER-CCLEANER.DAT"])
        key_path = "HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner"
        plugin = ccleaner.CCleanerPlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry,
            key_path,
            plugin,
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:ccleaner:update",
            "key_path": key_path,
            "update_time": "2013-07-13T10:03:14",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "configuration": [
                "(App)Cookies: True",
                "(App)Delete Index.dat files: True",
                "(App)History: True",
                "(App)Last Download Location: True",
                "(App)Other Explorer MRUs: True",
                "(App)Recent Documents: True",
                "(App)Recently Typed URLs: True",
                "(App)Run (in Start Menu): True",
                "(App)Temporary Internet Files: True",
                "(App)Thumbnail Cache: True",
                "CookiesToSave: *.piriform.com",
                "WINDOW_HEIGHT: 524",
                "WINDOW_LEFT: 146",
                "WINDOW_MAX: 0",
                "WINDOW_TOP: 102",
                "WINDOW_WIDTH: 733",
            ],
            "data_type": "windows:registry:ccleaner:configuration",
            "key_path": key_path,
            "last_written_time": "2013-07-13T14:03:26.8616882+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
