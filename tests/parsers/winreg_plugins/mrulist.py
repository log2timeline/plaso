#!/usr/bin/env python3
"""Tests for the MRUList Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import mrulist

from tests.parsers.winreg_plugins import test_lib


class TestMRUListStringWindowsRegistryPlugin(test_lib.RegistryPluginTestCase):
    """Tests for the string MRUList Windows Registry plugin."""

    def _CreateTestKey(self):
        """Creates Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2012-08-28 09:23:49.002031")

        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "MRU",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1456,
            relative_key_path="Software\\Microsoft\\Some Windows\\InterestingApp\\MRU",
        )
        value_data = b"a\x00c\x00b\x00\x00\x00"
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "MRUList",
            data=value_data,
            data_type=dfwinreg_definitions.REG_SZ,
            offset=123,
        )
        registry_key.AddValue(registry_value)

        value_data = "Some random text here".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "a", data=value_data, data_type=dfwinreg_definitions.REG_SZ, offset=1892
        )
        registry_key.AddValue(registry_value)

        value_data = "c:/evil.exe\x00".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "b", data=value_data, data_type=dfwinreg_definitions.REG_BINARY, offset=612
        )
        registry_key.AddValue(registry_value)

        value_data = "C:/looks_legit.exe".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "c", data=value_data, data_type=dfwinreg_definitions.REG_SZ, offset=1001
        )
        registry_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = mrulist.MRUListStringWindowsRegistryPlugin()

        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "MRUlist",
            key_path_prefix="HKEY_CURRENT_USER",
            relative_key_path="Software\\Microsoft\\Some Windows\\InterestingApp\\MRU",
        )
        result = self._CheckFiltersOnKeyPath(plugin, registry_key)
        self.assertFalse(result)

        registry_value = dfwinreg_fake.FakeWinRegistryValue("MRUList")
        registry_key.AddValue(registry_value)

        registry_value = dfwinreg_fake.FakeWinRegistryValue("a")
        registry_key.AddValue(registry_value)

        result = self._CheckFiltersOnKeyPath(plugin, registry_key)
        self.assertTrue(result)

        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\DesktopStreamMRU",
        )

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = mrulist.MRUListStringWindowsRegistryPlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

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
            "data_type": "windows:registry:mrulist",
            "entries": [
                "Index: 1 [MRU Value a]: Some random text here",
                "Index: 2 [MRU Value c]: C:/looks_legit.exe",
                "Index: 3 [MRU Value b]: c:/evil.exe",
            ],
            "key_path": (
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Some Windows\\InterestingApp\\"
                "MRU"
            ),
            "last_written_time": "2012-08-28T09:23:49.0020310+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


class TestMRUListShellItemListWindowsRegistryPlugin(test_lib.RegistryPluginTestCase):
    """Tests for the shell item list MRUList Windows Registry plugin."""

    _MRULIST_VALUE_DATA = b"a\x00\x00\x00"

    _A_VALUE_DATA = (
        b"\x14\x00\x1f\x00\xe0O\xd0 \xea:i\x10\xa2\xd8\x08\x00+00\x9d\x19\x00#C:\\\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\xee\x15"
        b"\x001\x00\x00\x00\x00\x00.>z`\x10\x80Winnt\x00\x00\x18\x001\x00\x00\x00\x00"
        b"\x00.>\xe4b\x10\x00Profiles\x00\x00%\x001\x00\x00\x00\x00\x00.>\xe4b\x10\x00"
        b"Administrator\x00ADMINI~1\x00\x17\x001\x00\x00\x00\x00\x00.>\xe4b\x10\x00"
        b"Desktop\x00\x00\x00\x00"
    )

    def _CreateTestKey(self):
        """Creates MRUList Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2012-08-28 09:23:49.002031")

        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "DesktopStreamMRU",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1456,
            relative_key_path=(
                "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\"
                "DesktopStreamMRU"
            ),
        )
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "MRUList",
            data=self._MRULIST_VALUE_DATA,
            data_type=dfwinreg_definitions.REG_SZ,
            offset=123,
        )
        registry_key.AddValue(registry_value)

        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "a",
            data=self._A_VALUE_DATA,
            data_type=dfwinreg_definitions.REG_BINARY,
            offset=612,
        )
        registry_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = mrulist.MRUListShellItemListWindowsRegistryPlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\DesktopStreamMRU",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = mrulist.MRUListShellItemListWindowsRegistryPlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Explorer\\DesktopStreamMRU"
        )
        # Check MRUList event data.
        expected_event_values = {
            "data_type": "windows:registry:mrulist",
            "entries": [
                "Index: 1 [MRU Value a]: Shell item path: <My Computer> "
                "C:\\\\Winnt\\\\Profiles\\\\Administrator\\\\Desktop"
            ],
            "key_path": expected_key_path,
            "last_written_time": "2012-08-28T09:23:49.0020310+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)

        # Check Shell item event data.
        expected_event_values = {
            "access_time": None,
            "creation_time": None,
            "data_type": "windows:shell_item:file_entry",
            "modification_time": "2011-01-14T12:03:52+00:00",
            "name": "Winnt",
            "origin": expected_key_path,
            "shell_item_path": "<My Computer> C:\\\\Winnt",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
