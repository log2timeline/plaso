#!/usr/bin/env python3
"""Tests for the PuTTY Windows Registry plugins."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import putty

from tests.parsers.winreg_plugins import test_lib


class PuTTYSessionsPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the PuTTY sessions Windows Registry plugin."""

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
            relative_key_path="Software\\SimonTatham\\PuTTY\\Sessions",
        )

        filetime.CopyFromDateTimeString("2018-08-15 10:12:13.234567")
        session_subkey = dfwinreg_fake.FakeWinRegistryKey(
            "my%20server", last_written_time=filetime.timestamp, offset=2048
        )
        registry_key.AddSubkey("my%20server", session_subkey)

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

        value_data = "ssh".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Protocol", data=value_data, data_type=dfwinreg_definitions.REG_SZ
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
        plugin = putty.PuTTYSessionsPlugin()

        self._AssertFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY\\Sessions"
        )

        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_CURRENT_USER",
            "Software\\SimonTatham\\PuTTY\\Sessions\\my%20server",
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTYgen\\Sessions"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_LOCAL_MACHINE", "Software\\SimonTatham\\PuTTY\\Sessions"
        )

    def testProcessWithRegistryFile(self):
        """Tests the Process function on a Windows Registry file.

        PuTTY 0.83 was installed on a Windows Server 2025 VM; the session subkeys
        were written with the values PuTTY saves (the saved sessions were not
        created through the PuTTY user interface).
        """
        test_file_entry = self._GetTestFileEntry(["NTUSER-PUTTY.DAT"])
        key_path = "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions"
        plugin = putty.PuTTYSessionsPlugin()

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
        self.assertEqual(event_data.data_type, "windows:registry:putty:session")
        self.assertEqual(event_data.hostname, "10.77.0.30")
        self.assertEqual(event_data.port_number, 22)
        self.assertEqual(event_data.username, "labadmin")

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = putty.PuTTYSessionsPlugin()
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

        expected_key_path = "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions"
        expected_event_values = {
            "data_type": "windows:registry:putty:session",
            "hostname": "server.example.com",
            "key_path": f"{expected_key_path:s}\\my%20server",
            "last_written_time": "2018-08-15T10:12:13.2345670+00:00",
            "port_number": 2222,
            "protocol": "ssh",
            "username": "admin",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:putty:session",
            "hostname": None,
            "key_path": f"{expected_key_path:s}\\wrong%20types",
            "port_number": None,
            "protocol": None,
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


class PuTTYSSHHostKeysPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the PuTTY SSH host keys Windows Registry plugin."""

    def _CreateTestKey(self):
        """Creates Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2018-08-15 10:11:12.123456")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "SshHostKeys",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1024,
            relative_key_path="Software\\SimonTatham\\PuTTY\\SshHostKeys",
        )

        # Default value, which is ignored.
        value_data = "default".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        registry_key.AddValue(registry_value)

        value_data = "0x10001,0xc1d2e3f4".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "rsa2@22:server.example.com",
            data=value_data,
            data_type=dfwinreg_definitions.REG_SZ,
        )
        registry_key.AddValue(registry_value)

        value_data = "0x1a2b,0x3c4d".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "ssh-ed25519@2222:192.168.1.10",
            data=value_data,
            data_type=dfwinreg_definitions.REG_SZ,
        )
        registry_key.AddValue(registry_value)

        # Value of the wrong type.
        value_data = (1).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "rsa2@22:wrong.example.com",
            data=value_data,
            data_type=dfwinreg_definitions.REG_DWORD,
        )
        registry_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = putty.PuTTYSSHHostKeysPlugin()

        self._AssertFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY\\SshHostKeys"
        )

        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", "Bogus")
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY\\Sessions"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY\\SshHostCAs"
        )

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = putty.PuTTYSSHHostKeysPlugin()
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
            "data_type": "windows:registry:putty:ssh_host_keys",
            "entries": ("rsa2@22:server.example.com ssh-ed25519@2222:192.168.1.10"),
            "key_path": (
                "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\SshHostKeys"
            ),
            "last_written_time": "2018-08-15T10:11:12.1234560+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
