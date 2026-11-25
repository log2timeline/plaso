#!/usr/bin/env python3
"""Tests for the AMCache Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake
from dfwinreg import regf as dfwinreg_regf

from plaso.parsers.winreg_plugins import amcache

from tests.parsers.winreg_plugins import test_lib


class AMCachePluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the AMCache.hve Windows Registry plugin."""

    def _CreateTestKey(self):
        """Creates Registry keys and values for testing.

        The values are hand-written in the format Windows uses, with value data
        that is malformed or of an unexpected type.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        filetime = dfdatetime_filetime.Filetime()
        filetime.CopyFromDateTimeString("2026-11-15 04:56:22.123456")

        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "Root", last_written_time=filetime.timestamp, relative_key_path="Root"
        )
        test_values = {
            "InventoryApplication": {
                "HiddenArp": (dfwinreg_definitions.REG_DWORD, b"\x01\x00\x00\x00"),
                "InstallDate": (dfwinreg_definitions.REG_SZ, "".encode("utf-16-le")),
                "InstallDateMsi": (dfwinreg_definitions.REG_SZ, b"\x00\xd8"),
                "Language": (dfwinreg_definitions.REG_SZ, "1033".encode("utf-16-le")),
                "MsiInstallDate": (
                    dfwinreg_definitions.REG_MULTI_SZ,
                    "11/14/2026 00:00:00\x00\x00".encode("utf-16-le"),
                ),
                # Value data that is not a valid UTF-16 little-endian string.
                "Name": (dfwinreg_definitions.REG_SZ, b"\x00\xd8"),
                # An integer where a string is expected.
                "Publisher": (dfwinreg_definitions.REG_DWORD, b"\x01\x00\x00\x00"),
            },
            "InventoryApplicationFile": {
                "Name": (dfwinreg_definitions.REG_SZ, b"\x00\xd8"),
            },
            "InventoryApplicationShortcut": {},
            # A key with a name similar to that of a supported key.
            "InventoryApplicationShortcuts": {
                "ShortcutPath": (
                    dfwinreg_definitions.REG_SZ,
                    "C:\\a.lnk".encode("utf-16-le"),
                ),
            },
            "InventoryDeviceContainer": {
                "IsActive": (dfwinreg_definitions.REG_SZ, "maybe".encode("utf-16-le")),
                "IsPaired": (dfwinreg_definitions.REG_SZ, "TRUE".encode("utf-16-le")),
                "State": (dfwinreg_definitions.REG_SZ, "nine".encode("utf-16-le")),
            },
            "InventoryDevicePnp": {
                # A date in an unsupported format.
                "DriverVerDate": (
                    dfwinreg_definitions.REG_SZ,
                    "2006/06/21".encode("utf-16-le"),
                ),
                # A date that does not exist.
                "FirstInstallDate": (
                    dfwinreg_definitions.REG_SZ,
                    "02-30-2026".encode("utf-16-le"),
                ),
                "InstallDate": (dfwinreg_definitions.REG_DWORD, b"\x01\x00\x00\x00"),
                "Model": (dfwinreg_definitions.REG_BINARY, b"\x01\x02"),
            },
            "InventoryDriverBinary": {
                # An integer of an unsupported size.
                "DriverCheckSum": (dfwinreg_definitions.REG_DWORD, b"\x01\x02"),
                "DriverInBox": (dfwinreg_definitions.REG_SZ, "1".encode("utf-16-le")),
                "DriverLastWriteTime": (
                    dfwinreg_definitions.REG_SZ,
                    "01/14/2026 18:34:08".encode("utf-16-le"),
                ),
                # Binary data where an integer is expected.
                "DriverTimeStamp": (dfwinreg_definitions.REG_BINARY, b"\x01\x02"),
                # An integer with the most significant bit set.
                "ImageSize": (dfwinreg_definitions.REG_DWORD, b"\x00\x00\x00\x80"),
            },
            "InventoryDriverPackage": {
                "Date": (dfwinreg_definitions.REG_SZ, "2016-5-25".encode("utf-16-le")),
            },
        }
        for key_name, values in test_values.items():
            inventory_key = dfwinreg_fake.FakeWinRegistryKey(
                key_name, last_written_time=filetime.timestamp
            )
            registry_key.AddSubkey(key_name, inventory_key)

            sub_key = dfwinreg_fake.FakeWinRegistryKey(
                "c:/test/entry", last_written_time=filetime.timestamp
            )
            inventory_key.AddSubkey("c:/test/entry", sub_key)

            for value_name, (data_type, data) in values.items():
                registry_value = dfwinreg_fake.FakeWinRegistryValue(
                    value_name, data=data, data_type=data_type
                )
                sub_key.AddValue(registry_value)

        return registry_key

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = amcache.AMCachePlugin()

        self._AssertFiltersOnKeyPath(plugin, "", "Root")
        self._AssertNotFiltersOnKeyPath(plugin, "", "Root\\File")

        self._AssertNotFiltersOnKeyPath(plugin, "", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        test_file_entry = self._GetTestFileEntry(["winreg", "Amcache.hve"])

        file_object = test_file_entry.GetFileObject()

        registry_file = dfwinreg_regf.REGFWinRegistryFile(ascii_codepage="cp1252")
        registry_file.Open(file_object)

        registry_key = registry_file.GetKeyByPath("\\Root")

        plugin = amcache.AMCachePlugin()
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4096)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_full_path = (
            "c:\\users\\user\\appdata\\local\\temp\\chocolatey\\"
            "is-f4510.tmp\\idafree50.tmp"
        )
        expected_event_values = {
            "application_key_last_written_time": None,
            "data_type": "windows:registry:amcache",
            "file_creation_time": "2017-08-01T12:43:35.1772758+00:00",
            "file_modification_time": "2017-08-01T12:43:35.3024523+00:00",
            "full_path": expected_full_path,
            "installation_time": None,
            "last_written_time": "2017-08-01T12:43:35.3715211+00:00",
            "link_time": "1992-06-19T22:22:17+00:00",
            "msi_installation_time": None,
            "sha1": "82274eef0911a948f91425f5e5b0e730517fe75e",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1420)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:programs",
            "entry_type": "AddRemoveProgram",
            "file_paths": [
                "c:\\program files (x86)\\fileinsight\\plugins",
                "c:\\program files (x86)\\fileinsight\\plugins\\anomaly chart",
                "c:\\program files (x86)\\fileinsight",
            ],
            "installation_time": "2017-08-01T12:52:59+00:00",
            "name": "FileInsight - File analysis tool",
            "publisher": "McAfee Inc.",
            "uninstall_key": [
                "HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Microsoft\\Windows\\"
                "CurrentVersion\\Uninstall\\FileInsight"
            ],
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4079)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:application",
            "entry_source": "AddRemoveProgram",
            "installation_os_version": "10.0.0.14393",
            "installation_time": "2017-08-01T12:52:59+00:00",
            "is_hidden": None,
            "language_code": None,
            "last_written_time": "2017-08-03T11:34:09.3419325+00:00",
            "msi_installation_time": None,
            "name": "FileInsight - File analysis tool",
            "program_identifier": "000078d7a1eaa34e32db4e775fc9e5b293e20000ffff",
            "publisher": "McAfee Inc.",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2372)
        self.CheckEventData(event_data, expected_event_values)

        # The InstallDateMsi value of this application is a multi-string.
        expected_event_values = {
            "data_type": "windows:registry:amcache:application",
            "entry_source": "Msi",
            "installation_time": "2017-08-01T00:00:00+00:00",
            "is_hidden": True,
            "language_code": 1033,
            "msi_installation_time": "2017-08-01T00:00:00+00:00",
            "msi_product_code": "{50a2bc33-c9cd-3bf1-a8ff-53c10a0b183c}",
            "name": "Microsoft Visual C++ 2015 x64 Minimum Runtime - 14.0.24215",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2356)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "checksum": 291739,
            "company_name": "VMware, Inc.",
            "data_type": "windows:registry:amcache:driver_binary",
            "driver_identifier": "00007e87dae0975cd5cf14c46522754d684ec9b4e6aa",
            "driver_package_strong_name": "vm3d.inf_amd64_509449bb136edd07",
            "driver_type": 8650826,
            "driver_version": "8.15.1.50",
            "file_modification_time": None,
            "filename": "vm3dmp.sys",
            "image_size": 229376,
            "inf_name": "oem9.inf",
            "is_in_box": None,
            "last_written_time": "2017-08-03T11:33:39.6215597+00:00",
            "link_time": "2016-12-14T10:50:34+00:00",
            "path": None,
            "product_name": "VMware SVGA 3D",
            "service": "vm3dmp",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3801)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "class_identifier": "{4d36e968-e325-11ce-bfc1-08002be10318}",
            "data_type": "windows:registry:amcache:driver_package",
            "device_class": "display",
            "directory": (
                "c:\\windows\\system32\\driverstore\\filerepository\\"
                "vm3d.inf_amd64_509449bb136edd07"
            ),
            "driver_package_strong_name": "vm3d.inf_amd64_509449bb136edd07",
            "driver_version": "8.15.1.50",
            "driver_version_time": "2016-12-13T00:00:00+00:00",
            "hardware_identifiers": (
                "pci\\ven_15ad&dev_0405&subsys_00000000&rev_00,"
                "pci\\ven_15ad&dev_0405&subsys_040515ad&rev_00"
            ),
            "inf_name": "oem9.inf",
            "last_written_time": "2017-08-03T11:33:50.9816194+00:00",
            "provider": "VMware, Inc.",
            "submission_identifier": "30099670_13602596144713971_1152921504626101403",
            "system_file": "vm3dmp.sys",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3961)
        self.CheckEventData(event_data, expected_event_values)

        # The Date value of the second driver package is "2016-5-25".
        expected_event_values = {
            "data_type": "windows:registry:amcache:driver_package",
            "driver_package_strong_name": "vmci.inf_amd64_64189b30c198ca23",
            "driver_version_time": "2016-05-25T00:00:00+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3962)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWindows10(self):
        """Tests the Process function on a Windows 10 1807 AMCache.hve file."""
        test_file_entry = self._GetTestFileEntry(["winreg", "win10-Amcache.hve"])

        file_object = test_file_entry.GetFileObject()

        registry_file = dfwinreg_regf.REGFWinRegistryFile(ascii_codepage="cp1252")
        registry_file.Open(file_object)

        registry_key = registry_file.GetKeyByPath("\\Root")

        plugin = amcache.AMCachePlugin()
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 372)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "application_key_last_written_time": "2019-12-17T05:30:28.2416496+00:00",
            "data_type": "windows:registry:amcache",
            "file_creation_time": None,
            "file_identifier": "000075c5a97f521f760e32a4a9639a653eed862e9c61",
            "file_modification_time": None,
            "filename": "svchost.exe",
            "full_path": "c:\\windows\\system32\\svchost.exe",
            "installation_time": None,
            "last_written_time": None,
            "link_time": "1997-01-10T22:26:24+00:00",
            "msi_installation_time": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 210)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "categories": "input.mouse",
            "container_identifier": "{103eb0c8-4fa6-51b4-38c4-83d2fe8201aa}",
            "data_type": "windows:registry:amcache:device_container",
            "friendly_name": None,
            "icon": "C:\\Windows\\System32\\DDORes.dll,-2212",
            "is_active": True,
            "is_connected": True,
            "is_machine_container": False,
            "is_networked": False,
            "is_paired": False,
            "last_written_time": "2019-12-16T20:45:18.3267979+00:00",
            "model_identifier": "{6acae7a0-4c1d-fec3-934e-992f289ff3db}",
            "model_name": "USB Tablet",
            "primary_category": "input.mouse",
            "state": 9,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 228)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "class_identifier": "{72631e54-78a4-11d0-bcf7-00aa00b7b32a}",
            "container_identifier": "{27db0821-3bf9-f71a-f96f-a53403857690}",
            "data_type": "windows:registry:amcache:device_pnp",
            "description": "Microsoft AC Adapter",
            "device_class": "battery",
            "device_instance_identifier": "acpi\\acpi0003\\0",
            "device_state": 32,
            "driver_identifier": "0000027adfdbfd29f9aed5f3ba1c27cdae89045b7567",
            "driver_name": "cmbatt.sys",
            "driver_package_strong_name": "cmbatt.inf_amd64_f8b93ac521ae56dc",
            "driver_version": "10.0.18362.1",
            "driver_version_time": "2006-06-21T00:00:00+00:00",
            "enumerator": "acpi",
            "first_installation_time": "2019-12-17T00:00:00+00:00",
            "hardware_identifiers": "acpi\\ven_acpi&dev_0003,acpi\\acpi0003,*acpi0003",
            "inf_name": "cmbatt.inf",
            "install_state": 0,
            "installation_time": "2019-12-17T00:00:00+00:00",
            "last_written_time": "2019-12-16T20:43:57.4951726+00:00",
            "manufacturer": "Microsoft",
            "matching_identifier": "acpi\\acpi0003",
            "model": "Microsoft AC Adapter",
            "parent_identifier": "acpi\\pnp0a03\\0",
            "problem_code": 0,
            "provider": "Microsoft",
            "service": "cmbatt",
            "stack_identifiers": "\\driver\\cmbatt,\\driver\\acpi",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 294)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWindowsServer2025(self):
        """Tests the Process function on a Windows Server 2025 AMCache.hve file.

        The test file is a copy of the AMCache.hve of a Windows Server 2025 lab
        system of which keys that are not needed by the test were removed, such
        as Root\\InventoryApplicationFile, to reduce its size.
        """
        test_file_entry = self._GetTestFileEntry(["winreg", "win2025-Amcache.hve"])

        file_object = test_file_entry.GetFileObject()

        registry_file = dfwinreg_regf.REGFWinRegistryFile(ascii_codepage="cp1252")
        registry_file.Open(file_object)

        registry_key = registry_file.GetKeyByPath("\\Root")

        plugin = amcache.AMCachePlugin()
        storage_writer = self._ParseKeyWithPlugin(
            registry_key, plugin, file_entry=test_file_entry
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1138)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:registry:amcache:application",
            "entry_source": "Msi",
            "installation_time": "2026-11-14T00:00:00+00:00",
            "is_hidden": False,
            "is_inbox_modern_application": None,
            "language_code": 1033,
            "last_written_time": "2026-11-15T04:56:04.9094488+00:00",
            "msi_installation_time": "2026-11-14T00:00:00+00:00",
            "msi_package_code": "{1DF327D3-777D-41B7-B5D6-51EDAEF2E1A2}",
            "msi_product_code": "{3B0346D3-155D-43E5-9561-B9BE51CF2EB6}",
            "name": "PuTTY release 0.85 (64-bit)",
            "program_identifier": "00007984ede6416c498aa2fd065d7d729e7e00000904",
            "publisher": "Simon Tatham",
            "uninstall_string": "MsiExec.exe /X{3B0346D3-155D-43E5-9561-B9BE51CF2EB6}",
            "version": "0.85.0.0",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 88)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "application_user_model_identifier": (
                "{F38BF404-1D43-42F2-9305-67DE0B28FC23}\\AzureArcSetup\\ArcSetup\\"
                "AzureArcSetup.exe"
            ),
            "data_type": "windows:registry:amcache:application_shortcut",
            "last_written_time": "2026-11-15T04:56:06.6677039+00:00",
            "program_identifier": None,
            "shortcut_path": (
                "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\"
                "Azure Arc Setup.lnk"
            ),
            "target_path": "C:\\WINDOWS\\AzureArcSetup\\ArcSetup\\AzureArcSetup.exe",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 173)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "container_identifier": "{1ef19a02-1b6b-b09b-c5b7-834a60d3c615}",
            "data_type": "windows:registry:amcache:device_container",
            "is_active": True,
            "is_connected": False,
            "last_written_time": "2026-11-15T04:56:20.7279029+00:00",
            "model_name": "Microsoft Remote Display Adapter",
            "state": 8,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 237)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:device_pnp",
            "device_instance_identifier": "usb\\root_hub\\4&2e134bf2&0",
            "driver_name": "usbhub.sys",
            "driver_version_time": "2006-06-21T00:00:00+00:00",
            "first_installation_time": "2026-11-06T00:00:00+00:00",
            "installation_time": "2026-11-06T00:00:00+00:00",
            "last_written_time": "2026-11-15T04:56:20.5852753+00:00",
            "location_paths": (
                "pciroot(0)#pci(0102)#usbroot(0),"
                "acpi(_sb_)#acpi(pci0)#pci(0102)#usbroot(0)"
            ),
            "model": "USB Root Hub",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 353)
        self.CheckEventData(event_data, expected_event_values)

        # The DriverTimeStamp value of this driver binary has its most
        # significant bit set.
        expected_event_values = {
            "checksum": 325325,
            "company_name": "Microsoft Corporation",
            "data_type": "windows:registry:amcache:driver_binary",
            "driver_identifier": "0000c7dea815b5f548a7619f4811d01c0b8af7bd7bf1",
            "driver_type": 8650778,
            "driver_version": "10.0.26100.1150",
            "file_modification_time": "2026-01-14T18:34:08+00:00",
            "filename": "1394ohci.sys",
            "image_size": 294912,
            "is_in_box": True,
            "is_kernel_mode": True,
            "is_signed": True,
            "last_written_time": "2026-11-15T04:56:22.5686542+00:00",
            "link_time": "2069-02-01T20:03:29+00:00",
            "path": "c:\\windows\\system32\\drivers\\1394ohci.sys",
            "product_name": "Microsoft® Windows® Operating System",
            "product_version": "10.0.26100.1150",
            "service": "1394ohci",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 749)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithMalformedValues(self):
        """Tests the Process function on malformed inventory values."""
        registry_key = self._CreateTestKey()

        plugin = amcache.AMCachePlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        # 17 default Windows Registry events, one for every key, and 7 inventory
        # events. The InventoryApplicationShortcuts key is not an inventory key.
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 24)

        # 12 warnings of the inventory values and 3 of the default Windows
        # Registry events of the keys with a value that cannot be decoded.
        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 15)

        event_data_per_type = {}
        for event_data in storage_writer.GetAttributeContainers("event_data"):
            event_data_per_type.setdefault(event_data.data_type, []).append(event_data)

        self.assertEqual(len(event_data_per_type["windows:registry:key_value"]), 17)

        expected_event_values = {
            "data_type": "windows:registry:amcache",
            "filename": None,
        }
        event_data = event_data_per_type["windows:registry:amcache"][0]
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:application",
            "installation_time": None,
            "is_hidden": True,
            "language_code": 1033,
            "last_written_time": "2026-11-15T04:56:22.1234560+00:00",
            "msi_installation_time": "2026-11-14T00:00:00+00:00",
            "name": None,
            "publisher": None,
        }
        event_data = event_data_per_type["windows:registry:amcache:application"][0]
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:application_shortcut",
            "last_written_time": "2026-11-15T04:56:22.1234560+00:00",
            "shortcut_path": None,
        }
        event_data = event_data_per_type[
            "windows:registry:amcache:application_shortcut"
        ][0]
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "container_identifier": "c:/test/entry",
            "data_type": "windows:registry:amcache:device_container",
            "is_active": None,
            "is_paired": True,
            "state": None,
        }
        event_data = event_data_per_type["windows:registry:amcache:device_container"][0]
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:device_pnp",
            "device_instance_identifier": "c:\\test\\entry",
            "driver_version_time": None,
            "first_installation_time": None,
            "installation_time": None,
            "model": None,
        }
        event_data = event_data_per_type["windows:registry:amcache:device_pnp"][0]
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "checksum": None,
            "data_type": "windows:registry:amcache:driver_binary",
            "driver_identifier": None,
            "file_modification_time": "2026-01-14T18:34:08+00:00",
            "image_size": 2147483648,
            "is_in_box": True,
            "link_time": None,
            "path": "c:\\test\\entry",
        }
        event_data = event_data_per_type["windows:registry:amcache:driver_binary"][0]
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:registry:amcache:driver_package",
            "driver_package_strong_name": "c:/test/entry",
            "driver_version_time": "2016-05-25T00:00:00+00:00",
        }
        event_data = event_data_per_type["windows:registry:amcache:driver_package"][0]
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
