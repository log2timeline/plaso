#!/usr/bin/env python3
"""Tests for the WinSCP sessions Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import winscp

from tests.parsers.winreg_plugins import test_lib


class WinSCPSessionsPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the WinSCP sessions Windows Registry plugin."""

    def _CreateTestKey(self):
        """Creates Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2018-08-15 10:11:12.123456")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "Sessions",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1024,
            relative_key_path="Software\\Martin Prikryl\\WinSCP 2\\Sessions",
        )

        filetime.CopyFromDateTimeString("2018-08-15 10:12:13.234567")
        session_subkey = dfwinreg_fake.FakeWinRegistryKey(
            "admin@server.example.com",
            last_written_time=filetime.timestamp,
            offset=2048,
        )
        registry_key.AddSubkey("admin@server.example.com", session_subkey)

        value_data = "server.example.com".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "HostName", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        session_subkey.AddValue(registry_value)

        value_data = (2222).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "PortNumber", data=value_data, data_type=dfwinreg_definitions.REG_DWORD
        )
        session_subkey.AddValue(registry_value)

        value_data = "admin".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "UserName", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        session_subkey.AddValue(registry_value)

        # Session with values of the wrong type.
        session_subkey = dfwinreg_fake.FakeWinRegistryKey(
            "wrong%20types", last_written_time=filetime.timestamp, offset=4096
        )
        registry_key.AddSubkey("wrong%20types", session_subkey)

        value_data = (1).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "HostName", data=value_data, data_type=dfwinreg_definitions.REG_DWORD
        )
        session_subkey.AddValue(registry_value)

        value_data = "22".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "PortNumber", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        session_subkey.AddValue(registry_value)

        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "UserName", data=b"\x01\x02", data_type=dfwinreg_definitions.REG_BINARY
        )
        session_subkey.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = winscp.WinSCPSessionsPlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Martin Prikryl\\WinSCP 2\\Sessions",
        )

        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\Martin Prikryl\\WinSCP 2"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Martin Prikryl\\WinSCP 2\\Configuration",
        )
        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\Martin Prikryl\\WinSCP 2\\Sessions\\admin@server.example.com",
        )
        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_LOCAL_MACHINE",
            "Software\\Martin Prikryl\\WinSCP 2\\Sessions",
        )

    def testProcessWithRegistryFile(self):
        """Tests the Process function on a Windows Registry file.

        WinSCP 6.7.1 (portable) was run on a Windows Server 2025 VM; the session
        subkeys were written with the values WinSCP saves (the saved sessions were
        not created through the WinSCP user interface).
        """
        test_file_entry = self._GetTestFileEntry(["NTUSER-WINSCP.DAT"])
        key_path = "HKEY_CURRENT_USER\\Software\\Martin Prikryl\\WinSCP 2\\Sessions"
        plugin = winscp.WinSCPSessionsPlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry, key_path, plugin
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

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(event_data.data_type, "windows:registry:winscp:session")
        self.assertEqual(event_data.hostname, "10.77.0.30")
        self.assertEqual(event_data.port_number, 22)
        self.assertEqual(event_data.username, "labadmin")

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = winscp.WinSCPSessionsPlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

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

        expected_key_path = (
            "HKEY_CURRENT_USER\\Software\\Martin Prikryl\\WinSCP 2\\Sessions"
        )
        expected_event_values = {
            "data_type": "windows:registry:winscp:session",
            "hostname": "server.example.com",
            "key_path": f"{expected_key_path:s}\\admin@server.example.com",
            "last_written_time": "2018-08-15T10:12:13.2345670+00:00",
            "port_number": 2222,
            "username": "admin",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:winscp:session",
            "hostname": None,
            "key_path": f"{expected_key_path:s}\\wrong%20types",
            "port_number": None,
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
