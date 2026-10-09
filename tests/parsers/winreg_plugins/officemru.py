#!/usr/bin/env python3
"""Tests for the Microsoft Office MRUs Windows Registry plugin."""

import time
import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import officemru

from tests.parsers.winreg_plugins import test_lib


class OfficeMRUPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the Microsoft Office MRUs Windows Registry plugin."""

    def _CreateTestKey(self, value_string):
        """Creates a Registry key with a single Office MRU item value.

        Args:
          value_string (str): data of the 'Item 1' REG_SZ value.

        Returns:
          dfwinreg.WinRegistryKey: Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2012-03-13 18:27:15")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "File MRU",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1456,
            relative_key_path=("Software\\Microsoft\\Office\\14.0\\Word\\File MRU"),
        )

        value_data = value_string.encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Item 1", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        registry_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = officemru.OfficeMRUPlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\Access\\File MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\Access\\Place MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\Excel\\File MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\Excel\\Place MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\PowerPoint\\File MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\PowerPoint\\Place MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\Word\\File MRU",
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Microsoft\\Office\\14.0\\Word\\Place MRU",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        test_file_entry = self._GetTestFileEntry(["NTUSER-WIN7.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU"
        )
        plugin = officemru.OfficeMRUPlugin()

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
            "data_type": "windows:registry:office_mru_list",
            "entries": (
                "Item 1: [F00000000][T01CD0146EA1EADB0][O00000000]*"
                "C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\"
                "SA-23E Mitchell-Hyundyne Starfury.docx "
                "Item 2: [F00000000][T01CD00921FC127F0][O00000000]*"
                "C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\Earthforce "
                "SA-26 Thunderbolt Star Fury.docx "
                "Item 3: [F00000000][T01CD009208780140][O00000000]*"
                "C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\StarFury.docx "
                "Item 4: [F00000000][T01CCFE0B22DA9EF0][O00000000]*"
                "C:\\Users\\nfury\\Documents\\VIBRANIUM.docx "
                "Item 5: [F00000000][T01CCFCBA595DFC30][O00000000]*"
                "C:\\Users\\nfury\\Documents\\ADAMANTIUM-Background.docx"
            ),
            "last_written_time": "2012-03-13T18:27:15.0898020+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 5)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:office_mru",
            "key_path": key_path,
            "last_written_time": "2012-03-13T18:27:15.0830000+00:00",
            "value_string": (
                "[F00000000][T01CD0146EA1EADB0][O00000000]*"
                "C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\"
                "SA-23E Mitchell-Hyundyne Starfury.docx"
            ),
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithSingleValue(self):
        """Tests the Process function on a created key with a single value."""
        value_string = (
            "[F00000000][T01CD0146EA1EADB0][O00000000]*"
            "C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\"
            "SA-23E Mitchell-Hyundyne Starfury.docx"
        )
        registry_key = self._CreateTestKey(value_string)

        plugin = officemru.OfficeMRUPlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:office_mru",
            "key_path": "HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\"
            "Word\\File MRU",
            "last_written_time": "2012-03-13T18:27:15.0830000+00:00",
            "value_string": value_string,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithLongValue(self):
        """Tests that parsing a long value does not become superlinear.

        A value that holds many repeated '[F00000000][T...]' segments and no
        file name separator previously caused the item value expression to
        backtrack superlinearly, so parsing a single value took quadratic time.
        """
        value_string = "[F00000000][T0123456789ABCDEF]" * 32000
        registry_key = self._CreateTestKey(value_string)

        plugin = officemru.OfficeMRUPlugin()

        start_time = time.perf_counter()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)
        elapsed_time = time.perf_counter() - start_time

        self.assertLess(elapsed_time, 5.0)

        # The value does not contain a file name separator, so only the MRU
        # list event is produced.
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

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(event_data.data_type, "windows:registry:office_mru_list")
        self.assertIsNone(event_data.entries)


if __name__ == "__main__":
    unittest.main()
