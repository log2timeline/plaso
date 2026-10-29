#!/usr/bin/env python3
"""Tests for the PuTTY Windows Registry plugins."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import putty

from tests.parsers.winreg_plugins import test_lib


class PuTTYSessionsPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the PuTTY saved sessions Windows Registry plugin."""

    def _CreateSessionSubkey(self, name, date_time_string, offset, values):
        """Creates a PuTTY saved session Registry key for testing.

        Args:
          name (str): name of the Registry key.
          date_time_string (str): last written date and time of the Registry key.
          offset (int): offset of the Registry key.
          values (list[tuple[str, int, object]]): name, data type and data of
              the Registry values.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString(date_time_string)
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            name, last_written_time=filetime.timestamp, offset=offset
        )

        for value_name, data_type, data in values:
            if data_type == dfwinreg_definitions.REG_SZ:
                value_data = data.encode("utf_16_le")
            else:
                value_data = data.to_bytes(4, "little")

            registry_value = dfwinreg_fake.FakeWinRegistryValue(
                value_name, data=value_data, data_type=data_type
            )
            registry_key.AddValue(registry_value)

        return registry_key

    def _CreateTestKey(self):
        """Creates PuTTY saved sessions Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2026-10-20 08:12:44.123456")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "Sessions",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=1024,
            relative_key_path="Software\\SimonTatham\\PuTTY\\Sessions",
        )

        subkey = self._CreateSessionSubkey(
            "Default%20Settings",
            "2026-10-18 14:02:10.000000",
            1456,
            [
                ("HostName", dfwinreg_definitions.REG_SZ, ""),
                ("PortNumber", dfwinreg_definitions.REG_DWORD_LITTLE_ENDIAN, 22),
                ("Protocol", dfwinreg_definitions.REG_SZ, "ssh"),
                ("PublicKeyFile", dfwinreg_definitions.REG_SZ, ""),
                ("UserName", dfwinreg_definitions.REG_SZ, ""),
            ],
        )
        registry_key.AddSubkey(subkey.name, subkey)

        subkey = self._CreateSessionSubkey(
            "web%20server",
            "2026-10-20 08:12:44.123456",
            2048,
            [
                ("HostName", dfwinreg_definitions.REG_SZ, "192.168.1.10"),
                ("PortNumber", dfwinreg_definitions.REG_DWORD_LITTLE_ENDIAN, 2222),
                ("Protocol", dfwinreg_definitions.REG_SZ, "ssh"),
                (
                    "PublicKeyFile",
                    dfwinreg_definitions.REG_SZ,
                    "C:\\Users\\john\\Documents\\web.ppk",
                ),
                ("UserName", dfwinreg_definitions.REG_SZ, "admin"),
            ],
        )
        registry_key.AddSubkey(subkey.name, subkey)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = putty.PuTTYSessionsPlugin()

        self._AssertFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY\\Sessions"
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE", "Bogus")

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

        expected_event_values = {
            "data_type": "windows:registry:putty:session",
            "remote_hostname": None,
            "key_path": (
                "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\"
                "Default%20Settings"
            ),
            "last_written_time": "2026-10-18T14:02:10.0000000+00:00",
            "port_number": 22,
            "protocol": "ssh",
            "public_key_file": None,
            "session_name": "Default Settings",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:putty:session",
            "remote_hostname": "192.168.1.10",
            "key_path": (
                "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\"
                "web%20server"
            ),
            "last_written_time": "2026-10-20T08:12:44.1234560+00:00",
            "port_number": 2222,
            "protocol": "ssh",
            "public_key_file": "C:\\Users\\john\\Documents\\web.ppk",
            "session_name": "web server",
            "username": "admin",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


class PuTTYSSHHostKeysPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the PuTTY SSH host keys Windows Registry plugin."""

    def _CreateTestKey(self):
        """Creates PuTTY SSH host keys Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2026-10-20 08:13:02.654321")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "SshHostKeys",
            key_path_prefix="HKEY_CURRENT_USER",
            last_written_time=filetime.timestamp,
            offset=4096,
            relative_key_path="Software\\SimonTatham\\PuTTY\\SshHostKeys",
        )

        for value_name, value_string in (
            ("ssh-ed25519@2222:192.168.1.10", "0x3b0a6e1d,0x5f2c9a4e"),
            ("rsa2@22:git.example.com", "0x10001,0xc4b2e7f1"),
        ):
            registry_value = dfwinreg_fake.FakeWinRegistryValue(
                value_name,
                data=value_string.encode("utf_16_le"),
                data_type=dfwinreg_definitions.REG_SZ,
            )
            registry_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = putty.PuTTYSSHHostKeysPlugin()

        self._AssertFiltersOnKeyPath(
            plugin, "HKEY_CURRENT_USER", "Software\\SimonTatham\\PuTTY\\SshHostKeys"
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE", "Bogus")

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
            "entries": ("ssh-ed25519@2222:192.168.1.10 rsa2@22:git.example.com"),
            "key_path": "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\SshHostKeys",
            "last_written_time": "2026-10-20T08:13:02.6543210+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
