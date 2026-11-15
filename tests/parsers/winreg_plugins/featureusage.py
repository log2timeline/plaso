#!/usr/bin/env python3
"""Tests for the Windows Explorer FeatureUsage Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import featureusage

from tests.parsers.winreg_plugins import test_lib


class FeatureUsagePluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the Windows Explorer FeatureUsage Windows Registry plugin."""

    _KEY_PATH = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FeatureUsage"

    def _CreateTestKey(self):
        """Creates Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2019-08-15 10:11:12.123456")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "AppSwitched",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1024,
            relative_key_path=f"{self._KEY_PATH:s}\\AppSwitched",
        )

        # Default value.
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "", data=b"", data_type=dfwinreg_definitions.REG_SZ
        )
        registry_key.AddValue(registry_value)

        value_data = (21).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Microsoft.Windows.Explorer",
            data=value_data,
            data_type=dfwinreg_definitions.REG_DWORD,
        )
        registry_key.AddValue(registry_value)

        value_data = (5).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\cmd.exe",
            data=value_data,
            data_type=dfwinreg_definitions.REG_DWORD,
        )
        registry_key.AddValue(registry_value)

        # Value of the wrong type.
        value_data = "3".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "C:\\Tools\\wrong_type.exe",
            data=value_data,
            data_type=dfwinreg_definitions.REG_SZ,
        )
        registry_key.AddValue(registry_value)

        # Value with malformed data.
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "C:\\Tools\\malformed.exe",
            data=b"\x01\x02",
            data_type=dfwinreg_definitions.REG_DWORD,
        )
        registry_key.AddValue(registry_value)

        # Value without data.
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "C:\\Tools\\empty.exe", data=b"", data_type=dfwinreg_definitions.REG_DWORD
        )
        registry_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = featureusage.FeatureUsagePlugin()

        for subkey_name in (
            "AppBadgeUpdated",
            "AppLaunch",
            "AppSwitched",
            "ShowJumpView",
            "TrayButtonClicked",
        ):
            self._AssertFiltersOnKeyPath(
                plugin, "HKEY_CURRENT_USER", f"{self._KEY_PATH:s}\\{subkey_name:s}"
            )

        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", self._KEY_PATH)
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", f"{self._KEY_PATH:s}\\Bogus"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", f"{self._KEY_PATH:s}\\AppLaunch\\Bogus"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", f"{self._KEY_PATH:s}2\\AppLaunch"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_LOCAL_MACHINE", f"{self._KEY_PATH:s}\\AppLaunch"
        )

    def testProcessWithRegistryFile(self):
        """Tests the Process function on a Windows Registry file.

        The test file is the NTUSER.DAT of a Windows 11 (build 26300) lab account.
        The FeatureUsage values were written by Windows Explorer after mouse clicks
        on the taskbar buttons of File Explorer and Notepad.
        """
        test_file_entry = self._GetTestFileEntry(["NTUSER-USERACTIVITY.DAT"])
        key_path = f"HKEY_CURRENT_USER\\{self._KEY_PATH:s}\\AppSwitched"
        plugin = featureusage.FeatureUsagePlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry, key_path, plugin
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
            "data_type": "windows:registry:explorer:feature_usage",
            "entries": [
                "Microsoft.Windows.Explorer: 4",
                "Microsoft.WindowsNotepad_8wekyb3d8bbwe!App: 4",
            ],
            "key_path": key_path,
            "last_written_time": "2026-11-15T00:49:03.0482260+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = featureusage.FeatureUsagePlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:explorer:feature_usage",
            "entries": [
                "Microsoft.Windows.Explorer: 21",
                "%WINDIR%\\System32\\cmd.exe: 5",
            ],
            "key_path": f"HKEY_CURRENT_USER\\{self._KEY_PATH:s}\\AppSwitched",
            "last_written_time": "2019-08-15T10:11:12.1234560+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithEmptyKey(self):
        """Tests the Process function on a key without values."""
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "ShowJumpView",
            key_path_prefix="HKEY_CURRENT_USER",
            relative_key_path=f"{self._KEY_PATH:s}\\ShowJumpView",
        )

        plugin = featureusage.FeatureUsagePlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertIsNone(event_data.entries)


if __name__ == "__main__":
    unittest.main()
