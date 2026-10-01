#!/usr/bin/env python3
"""Tests for the TypedURLsTime Windows Registry plugin."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import typedurlstime

from tests.parsers.winreg_plugins import test_lib


class TypedURLsTimePluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the TypedURLsTime Windows Registry plugin."""

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = typedurlstime.TypedURLsTimePlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Internet Explorer\\TypedURLsTime",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\TypedURLsTime"
        )
        plugin = typedurlstime.TypedURLsTimePlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry,
            key_path,
            plugin,
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:typedurlstime",
            "entry": "url1: http://www.catnews.com/",
            "key_path": key_path,
            "last_visited_time": "2016-10-05T09:47:50.9674171+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithoutContextKey(self):
        """Tests the Process function without the TypedURLs context key."""
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\TypedURLsTime"
        )

        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)

        plugin = typedurlstime.TypedURLsTimePlugin()
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:typedurlstime",
            "entry": "url1",
            "key_path": key_path,
            "last_visited_time": "2016-10-05T09:47:50.9674171+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithUnsupportedValueData(self):
        """Tests the Process function with unsupported value data."""
        test_file_entry = test_lib.TestFileEntry("NTUSER.DAT")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "TypedURLsTime",
            key_path_prefix="HKEY_CURRENT_USER",
            relative_key_path="Software\\Microsoft\\Internet Explorer\\TypedURLsTime",
        )
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "url1",
            data=b"\x01\x02\x03\x04",
            data_type=dfwinreg_definitions.REG_BINARY,
        )
        registry_key.AddValue(registry_value)

        plugin = typedurlstime.TypedURLsTimePlugin()
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)


if __name__ == "__main__":
    unittest.main()
