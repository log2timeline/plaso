#!/usr/bin/env python3
"""Tests for the BagMRU Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import bagmru

from tests.parsers.winreg_plugins import test_lib


class TestBagMRUWindowsRegistryPlugin(test_lib.RegistryPluginTestCase):
    """Tests for the BagMRU plugin."""

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = bagmru.BagMRUWindowsRegistryPlugin()

        self._AssertFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\Microsoft\\Windows\\Shell\\BagMRU"
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER\\Software\\Classes",
            "Local Settings\\Software\\Microsoft\\Windows\\Shell\\BagMRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER\\Software\\Classes",
            "Local Settings\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Local Settings\\Software\\Microsoft\\Windows\\Shell\\BagMRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Local Settings\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

    def testProcessWithNtUserDat(self):
        """Tests the Process function on a NTUSER.DAT file."""
        plugin = bagmru.BagMRUWindowsRegistryPlugin()
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU"
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)
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
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:bagmru",
            "entries": None,
            "key_path": key_path,
            "last_written_time": "2016-10-05T09:02:55.6114658+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithUsrClassDat(self):
        """Tests the Process function on an UsrClass.dat file."""
        plugin = bagmru.BagMRUWindowsRegistryPlugin()
        test_file_entry = self._GetTestFileEntry(["regf", "UsrClass.dat"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\"
            "Microsoft\\Windows\\Shell\\BagMRU"
        )
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 7)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:bagmru",
            "entries": (
                "Index: 1 [MRU Value 0]: Shell item path: <Control Panel> "
                "Index: 2 [MRU Value 1]: Shell item path: <My Computer>"
            ),
            "key_path": key_path,
            "last_written_time": "2016-10-09T20:04:37.8092483+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:bagmru",
            "entries": None,
            "key_path": f"{key_path:s}\\1\\0",
            "last_written_time": "2016-10-09T19:59:07.2344283+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 6)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
