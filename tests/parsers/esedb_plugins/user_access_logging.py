#!/usr/bin/env python3
"""Tests for the User Access Logging (UAL) ESE database file."""

import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers.esedb_plugins import user_access_logging

from tests.parsers.esedb_plugins import test_lib


class TestESEDBRecord:
    """ESE database record for testing.

    Attributes:
      number_of_values (int): number of values.
    """

    # Note: that the following functions do not follow the style guide
    # because they are part of the pyesedb record interface.
    # pylint: disable=invalid-name

    def __init__(self, values):
        """Initializes an ESE database record for testing.

        Args:
          values (list[tuple[str, bytes]]): column name and value data pairs.
        """
        super().__init__()
        self._values = values
        self.number_of_values = len(values)

    def get_column_name(self, value_entry):
        """Retrieves the column name of a specific value.

        Args:
          value_entry (int): value entry.

        Returns:
          str: column name.
        """
        return self._values[value_entry][0]

    def get_value_data(self, value_entry):
        """Retrieves the data of a specific value.

        Args:
          value_entry (int): value entry.

        Returns:
          bytes: value data.
        """
        return self._values[value_entry][1]


class TestESEDBTable:
    """ESE database table for testing.

    Attributes:
      name (str): name of the table.
      records (list[TestESEDBRecord]): records.
    """

    def __init__(self, name, records):
        """Initializes an ESE database table for testing.

        Args:
          name (str): name of the table.
          records (list[TestESEDBRecord]): records.
        """
        super().__init__()
        self.name = name
        self.records = records


class UserAccessLoggingESEDBPluginTest(test_lib.ESEDBPluginTestCase):
    """Tests for the User Access Logging (UAL) ESE Database plugin."""

    # pylint: disable=protected-access

    _GUID_BYTES = bytes(
        bytearray(
            [
                0xC9,
                0x8B,
                0x91,
                0x35,
                0x6D,
                0x19,
                0xEA,
                0x40,
                0x97,
                0x79,
                0x88,
                0x9D,
                0x79,
                0xB7,
                0x53,
                0xF0,
            ]
        )
    )

    def testProcessDatabase(self):
        """Tests processing the database."""
        plugin = user_access_logging.UserAccessLoggingESEDBPlugin()
        storage_writer = self._ParseESEDBFileWithPlugin(
            ["{C519A76A-D9B5-4F85-B667-5FAC08E0E1B4}.mdb"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 25)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:user_access_logging:system_identity",
            "creation_time": "2022-07-16T14:46:12.5700000+00:00",
            "operating_system_build": 17763,
            "system_dns_hostname": "DC-1",
            "system_domain_name": "WORKGROUP",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "access_time": "2022-07-16T15:02:52.7424758+00:00",
            "authenticated_username": "ual\\dc-1$",
            "client_name": None,
            "data_type": "windows:user_access_logging:clients",
            "insert_time": "2022-07-16T14:50:27.0773450+00:00",
            "role_identifier": "{ad495fc3-0eaa-413d-ba7d-8b13fa7ec598}",
            "role_name": "Active Directory Domain Services",
            "source_ip_address": "::1",
            "tenant_identifier": "{3facd7dc-85cc-495b-823f-6c96a9e1c40c}",
            "total_accesses": 62,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:user_access_logging:role_access",
            "first_seen_time": "2022-07-16T14:52:50.2088607+00:00",
            "last_seen_time": "2022-07-16T15:00:59.3156655+00:00",
            "role_identifier": "{10a9226f-50ee-49d8-a393-9a501d47ce04}",
            "role_name": "File Server",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 24)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:user_access_logging:dns",
            "hostname": "dc-1",
            "ip_address": "10.0.10.10",
            "last_seen_time": "2022-07-16T15:02:53.0830000+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 18)
        self.CheckEventData(event_data, expected_event_values)

    def testConvertGUIDToString(self):
        """Tests GUID to string conversion."""
        plugin = user_access_logging.UserAccessLoggingESEDBPlugin()

        guid_string = plugin._ConvertGUIDToString(self._GUID_BYTES)
        self.assertEqual(guid_string, "{35918bc9-196d-40ea-9779-889d79b753f0}")

    def testParseVirtualMachinesTable(self):
        """Tests the ParseVirtualMachinesTable function."""
        plugin = user_access_logging.UserAccessLoggingESEDBPlugin()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = parsers_mediator.ParserMediator()
        parser_mediator.SetStorageWriter(storage_writer)

        # Column names as defined in the VIRTUALMACHINES table of UAL databases.
        esedb_record = TestESEDBRecord(
            [("VmGuid", self._GUID_BYTES), ("BIOSGuid", bytes(range(16)))]
        )
        table = TestESEDBTable("VIRTUALMACHINES", [esedb_record])

        plugin.ParseVirtualMachinesTable(
            parser_mediator, database=object(), table=table
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        expected_event_values = {
            "bios_identifier": "{03020100-0504-0706-0809-0a0b0c0d0e0f}",
            "data_type": "windows:user_access_logging:virtual_machines",
            "vm_identifier": "{35918bc9-196d-40ea-9779-889d79b753f0}",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
