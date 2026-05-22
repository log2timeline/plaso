#!/usr/bin/env python3
"""Tests for the MountPoints2 Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import mountpoints

from tests.parsers.winreg_plugins import test_lib


class MountPoints2PluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the MountPoints2 Windows Registry plugin."""

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = mountpoints.MountPoints2Plugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            ("Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2"),
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Explorer\\MountPoints2"
        )
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)

        plugin = mountpoints.MountPoints2Plugin()
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
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

        expected_event_values = {
            "data_type": "windows:registry:mount_points2",
            "key_path": key_path,
            "label": None,
            "last_written_time": "2016-10-09T19:57:35.4892903+00:00",
            "name": "{8bff1c84-9188-11e5-824f-806e6f6e6963}",
            "server_name": "Drive",
            "share_name": None,
            "type": "Volume",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
