#!/usr/bin/env python3
"""Tests for the MSIE zone settings Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import msie_zones

from tests.parsers.winreg_plugins import test_lib


class MSIEZoneSettingsPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for Internet Settings zone settings plugin."""

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = msie_zones.MSIEZoneSettingsPlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            (
                "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\"
                "Lockdown_Zones"
            ),
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            (
                "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\"
                "Zones"
            ),
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            (
                "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\"
                "Lockdown_Zones"
            ),
        )
        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_LOCAL_MACHINE\\Software",
            ("Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones"),
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE\\Software", "Bogus")

    def testProcessWithLockdownZonesKeyInNtUserDat(self):
        """Tests the Process function on a Lockdown_Zones key in a NTUSER.DAT file."""
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Internet Settings\\Lockdown_Zones"
        )
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)

        plugin = msie_zones.MSIEZoneSettingsPlugin()
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
            "data_type": "windows:registry:msie_zone_settings",
            "key_path": f"{key_path:s}\\0 (My Computer)",
            "last_written_time": "2016-10-05T09:01:16.7367811+00:00",
            "settings": [
                ("1200", 3),
                ("1400", 1),
                ("CurrentLevel", 0),
                ("Description", "Your computer"),
                ("DisplayName", "Computer"),
                ("Flags", 33),
                ("Icon", "shell32.dll#0016"),
                ("LowIcon", "inetcpl.cpl#005422"),
                ("PMDisplayName", "Computer [Protected Mode]"),
            ],
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithZonesKeyInNtUserDat(self):
        """Tests the Process function on a Zones key in a NTUSER.DAT file."""
        test_file_entry = self._GetTestFileEntry(["regf", "NTUSER.DAT"])
        key_path = (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Internet Settings\\Zones"
        )
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)

        plugin = msie_zones.MSIEZoneSettingsPlugin()
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
            "data_type": "windows:registry:msie_zone_settings",
            "key_path": f"{key_path:s}\\0 (My Computer)",
            "last_written_time": "2016-10-05T09:01:16.7367811+00:00",
            "settings": [
                ("1200", 0),
                ("1400", 0),
                ("2001", 0),
                ("2004", 0),
                ("2007", 3),
                ("CurrentLevel", 0),
                ("Description", "Your computer"),
                ("DisplayName", "Computer"),
                ("Flags", 33),
                ("Icon", "shell32.dll#0016"),
                ("LowIcon", "inetcpl.cpl#005422"),
                ("PMDisplayName", "Computer [Protected Mode]"),
            ],
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithLockdownZonesKeyInSoftware(self):
        """Tests the Process function on a Lockdown_Zones key in a SOFTWARE file."""
        test_file_entry = self._GetTestFileEntry(["regf", "SOFTWARE"])
        key_path = (
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Internet Settings\\Lockdown_Zones"
        )
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)

        plugin = msie_zones.MSIEZoneSettingsPlugin()
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

        expected_settings = [
            ("1001", 1),
            ("1004", 3),
            ("1200", 3),
            ("1201", 3),
            ("1206", 0),
            ("1207", 3),
            ("1208", 3),
            ("1209", 3),
            ("120A", 3),
            ("120B", 0),
            ("1400", 1),
            ("1402", 0),
            ("1405", 0),
            ("1406", 0),
            ("1407", 1),
            ("1408", 3),
            ("1409", 3),
            ("140A", 0),
            ("1601", 0),
            ("1604", 0),
            ("1605", 0),
            ("1606", 0),
            ("1607", 0),
            ("1608", 0),
            ("1609", 1),
            ("160A", 0),
            ("160B", 0),
            ("1802", 0),
            ("1803", 0),
            ("1804", 0),
            ("1805", 0),
            ("1806", 0),
            ("1807", 0),
            ("1808", 0),
            ("1809", 3),
            ("180A", 0),
            ("180C", 0),
            ("180D", 0),
            ("180E", 0),
            ("180F", 0),
            ("1810", 3),
            ("1812", 0),
            ("1A00", 0),
            ("1A02", 0),
            ("1A03", 0),
            ("1A04", 3),
            ("1A05", 0),
            ("1A06", 0),
            ("1A10", 0),
            ("1C00", 0),
            ("2000", 0x00010000),
            ("2005", 3),
            ("2100", 3),
            ("2101", 3),
            ("2102", 3),
            ("2103", 3),
            ("2104", 3),
            ("2105", 3),
            ("2106", 3),
            ("2107", 3),
            ("2200", 3),
            ("2201", 3),
            ("2301", 3),
            ("2302", 3),
            ("2400", 0),
            ("2401", 0),
            ("2402", 0),
            ("2500", 3),
            ("2600", 0),
            ("2700", 3),
            ("2701", 3),
            ("2702", 3),
            ("2703", 3),
            ("2704", 3),
            ("2708", 3),
            ("2709", 3),
            ("270B", 3),
            ("270C", 3),
            ("270D", 3),
            ("CurrentLevel", 0),
            ("Description", "Your computer"),
            ("DisplayName", "Computer"),
            ("Flags", 33),
            ("Icon", "shell32.dll#0016"),
            ("LowIcon", "inetcpl.cpl#005422"),
            ("PMDisplayName", "Computer [Protected Mode]"),
        ]
        expected_event_values = {
            "data_type": "windows:registry:msie_zone_settings",
            "key_path": f"{key_path:s}\\0 (My Computer)",
            "last_written_time": "2013-08-22T15:37:08.5313209+00:00",
            "settings": expected_settings,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithZonesKeyInSoftware(self):
        """Tests the Process function on a Zones key in a SOFTWARE file."""
        test_file_entry = self._GetTestFileEntry(["SOFTWARE"])
        key_path = (
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Internet Settings\\Zones"
        )
        win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
        registry_key = win_registry.GetKeyByPath(key_path)

        plugin = msie_zones.MSIEZoneSettingsPlugin()
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

        expected_settings = [
            ("1001", 0),
            ("1004", 0),
            ("1200", 0),
            ("1201", 1),
            ("1206", 0),
            ("1207", 0),
            ("1208", 0),
            ("1209", 0),
            ("120A", 0),
            ("120B", 0),
            ("1400", 0),
            ("1402", 0),
            ("1405", 0),
            ("1406", 0),
            ("1407", 0),
            ("1408", 0),
            ("1409", 3),
            ("1601", 0),
            ("1604", 0),
            ("1605", 0),
            ("1606", 0),
            ("1607", 0),
            ("1608", 0),
            ("1609", 1),
            ("160A", 0),
            ("1802", 0),
            ("1803", 0),
            ("1804", 0),
            ("1805", 0),
            ("1806", 0),
            ("1807", 0),
            ("1808", 0),
            ("1809", 3),
            ("180A", 0),
            ("180C", 0),
            ("180D", 0),
            ("180E", 0),
            ("180F", 0),
            ("1A00", 0),
            ("1A02", 0),
            ("1A03", 0),
            ("1A04", 0),
            ("1A05", 0),
            ("1A06", 0),
            ("1A10", 0),
            ("1C00", 0x00020000),
            ("2000", 0),
            ("2001", 3),
            ("2004", 3),
            ("2005", 0),
            ("2007", 3),
            ("2100", 0),
            ("2101", 3),
            ("2102", 0),
            ("2103", 0),
            ("2104", 0),
            ("2105", 0),
            ("2106", 0),
            ("2107", 0),
            ("2200", 0),
            ("2201", 0),
            ("2300", 1),
            ("2301", 3),
            ("2400", 0),
            ("2401", 0),
            ("2402", 0),
            ("2500", 3),
            ("2600", 0),
            ("2700", 3),
            ("2701", 0),
            ("2702", 3),
            ("2703", 3),
            ("2708", 0),
            ("2709", 0),
            ("CurrentLevel", 0),
            ("Description", "Your computer"),
            ("DisplayName", "Computer"),
            ("Flags", 33),
            ("Icon", "shell32.dll#0016"),
            ("LowIcon", "inetcpl.cpl#005422"),
            ("PMDisplayName", "Computer [Protected Mode]"),
        ]
        expected_event_values = {
            "data_type": "windows:registry:msie_zone_settings",
            "key_path": f"{key_path:s}\\0 (My Computer)",
            "last_written_time": "2011-08-28T21:32:44.9376751+00:00",
            "settings": expected_settings,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
