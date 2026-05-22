#!/usr/bin/env python3
"""Tests for the TypedURLs Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import typedurls

from tests.parsers.winreg_plugins import test_lib


class TypedURLsPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the TypedURLs Windows Registry plugin."""

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = typedurls.TypedURLsPlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Internet Explorer\\TypedURLs",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

    def testProcessWithTypedPathsKey(self):
        """Tests the Process function on a TypedPaths key."""
        test_file_entry = self._GetTestFileEntry(["NTUSER-WIN7.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Explorer\\TypedPaths"
        )
        plugin = typedurls.TypedURLsPlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry,
            key_path,
            plugin,
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
            "data_type": "windows:registry:typedurls",
            "entries": ["url1: \\\\controller"],
            "key_path": key_path,
            "last_written_time": "2010-11-10T07:58:15.8116250+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithTypedURLsKey(self):
        """Tests the Process function on a TypedURLs key."""
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\TypedURLs"
        )
        plugin = typedurls.TypedURLsPlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry,
            key_path,
            plugin,
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
            "data_type": "windows:registry:typedurls",
            "entries": [
                "url1: http://www.catnews.com/",
                "url2: http://spotify.com/",
                "url3: http://pintrest.com/",
                "url4: http://webmail.student.greendale.xyz/",
                "url5: http://go.microsoft.com/fwlink/p/?LinkId=255141",
            ],
            "key_path": key_path,
            "last_written_time": "2016-10-05T09:47:50.9674171+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
