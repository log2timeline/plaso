#!/usr/bin/env python3
"""Tests for the LANDesk software monitoring Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import landesk

from tests.parsers.winreg_plugins import test_lib


class LANDeskSoftwareMonitoringPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the LANDesk software monitoring Windows Registry plugin."""

    _KEY_PATH = (
        "Software\\LANDesk\\ManagementSuite\\WinClient\\SoftwareMonitoring\\"
        "MonitorLog"
    )

    def _CreateFiletimeData(self, date_time_string):
        """Creates FILETIME value data.

        Args:
          date_time_string (str): date and time string.

        Returns:
          bytes: FILETIME value data.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString(date_time_string)
        return filetime.timestamp.to_bytes(8, "little")

    def _CreateTestKey(self):
        """Creates Registry keys and values for testing.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2016-06-15 08:00:00")
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "MonitorLog",
            key_path_prefix="HKEY_LOCAL_MACHINE",
            last_written_time=filetime.timestamp,
            offset=1024,
            relative_key_path=self._KEY_PATH,
        )

        filetime.CopyFromDateTimeString("2016-06-15 09:10:11.123456")
        subkey = dfwinreg_fake.FakeWinRegistryKey(
            "C:/Windows/System32/gsec.exe",
            last_written_time=filetime.timestamp,
            offset=2048,
        )
        registry_key.AddSubkey("C:/Windows/System32/gsec.exe", subkey)

        value_data = "DOMAIN\\username".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Current User", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        subkey.AddValue(registry_value)

        value_data = self._CreateFiletimeData("2016-06-01 07:06:05.123456")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "First Started",
            data=value_data,
            data_type=dfwinreg_definitions.REG_BINARY,
        )
        subkey.AddValue(registry_value)

        value_data = self._CreateFiletimeData("2016-06-15 09:10:11.654321")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Last Started",
            data=value_data,
            data_type=dfwinreg_definitions.REG_BINARY,
        )
        subkey.AddValue(registry_value)

        value_data = (5).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Total Runs", data=value_data, data_type=dfwinreg_definitions.REG_DWORD
        )
        subkey.AddValue(registry_value)

        # Subkey with a FILETIME value that is not set.
        subkey = dfwinreg_fake.FakeWinRegistryKey(
            "C:/Temp/zero.exe", last_written_time=filetime.timestamp, offset=3072
        )
        registry_key.AddSubkey("C:/Temp/zero.exe", subkey)

        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "First Started",
            data=bytes(8),
            data_type=dfwinreg_definitions.REG_BINARY,
        )
        subkey.AddValue(registry_value)

        # Subkey with values of the wrong type or size.
        subkey = dfwinreg_fake.FakeWinRegistryKey(
            "C:/Temp/wrong.exe", last_written_time=filetime.timestamp, offset=4096
        )
        registry_key.AddSubkey("C:/Temp/wrong.exe", subkey)

        value_data = (1).to_bytes(4, "little")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Current User", data=value_data, data_type=dfwinreg_definitions.REG_DWORD
        )
        subkey.AddValue(registry_value)

        value_data = "2016-06-01 07:06:05".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "First Started", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        subkey.AddValue(registry_value)

        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Last Started",
            data=b"\x01\x02\x03\x04",
            data_type=dfwinreg_definitions.REG_BINARY,
        )
        subkey.AddValue(registry_value)

        value_data = "5".encode("utf_16_le")
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Total Runs", data=value_data, data_type=dfwinreg_definitions.REG_SZ
        )
        subkey.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = landesk.LANDeskSoftwareMonitoringPlugin()

        self._AssertFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE", self._KEY_PATH)

        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE", "Bogus")
        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_LOCAL_MACHINE",
            "Software\\LANDesk\\ManagementSuite\\WinClient\\SoftwareMonitoring",
        )
        self._AssertNotFiltersOnKeyPath(
            plugin, "HKEY_LOCAL_MACHINE", f"{self._KEY_PATH:s}s"
        )
        self._AssertNotFiltersOnKeyPath(
            plugin,
            "HKEY_LOCAL_MACHINE",
            f"{self._KEY_PATH:s}\\C:/Windows/System32/gsec.exe",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_CURRENT_USER", self._KEY_PATH)

    def testProcess(self):
        """Tests the Process function."""
        registry_key = self._CreateTestKey()

        plugin = landesk.LANDeskSoftwareMonitoringPlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        # The 4-byte "Last Started" value produces a warning.
        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_key_path = f"HKEY_LOCAL_MACHINE\\{self._KEY_PATH:s}"
        expected_event_values = {
            "data_type": "windows:registry:landesk:software_monitoring",
            "first_execution_time": "2016-06-01T07:06:05.1234560+00:00",
            "key_path": expected_key_path,
            "last_execution_time": "2016-06-15T09:10:11.6543210+00:00",
            "last_written_time": "2016-06-15T09:10:11.1234560+00:00",
            "number_of_executions": 5,
            "path": "C:/Windows/System32/gsec.exe",
            "username": "DOMAIN\\username",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:landesk:software_monitoring",
            "first_execution_time": None,
            "key_path": expected_key_path,
            "path": "C:/Temp/zero.exe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:landesk:software_monitoring",
            "first_execution_time": None,
            "key_path": expected_key_path,
            "last_execution_time": None,
            "number_of_executions": None,
            "path": "C:/Temp/wrong.exe",
            "username": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
