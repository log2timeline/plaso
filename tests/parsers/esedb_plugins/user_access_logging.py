# -*- coding: utf-8 -*-
"""Tests for the User Access Logging (UAL) ESE database file."""

import unittest

from plaso.lib import definitions
from plaso.parsers.esedb_plugins import user_access_logging

from tests.parsers.esedb_plugins import test_lib


class UserAccessLoggingESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the User Access Logging (UAL) ESE Database plugin."""

  # pylint: disable=protected-access

  _GUID_BYTES = bytes(bytearray([
      0xc9, 0x8b, 0x91, 0x35, 0x6d, 0x19, 0xea, 0x40, 0x97, 0x79, 0x88, 0x9d,
      0x79, 0xb7, 0x53, 0xf0]))

  def testProcessDatabase(self):
    """Tests processing the database"""
    plugin = user_access_logging.UserAccessLoggingESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['{C519A76A-D9B5-4F85-B667-5FAC08E0E1B4}.mdb'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event')
    self.assertEqual(number_of_events, 42)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'windows:user_access_logging:system_identity',
        'operating_system_build': 17763,
        'system_dns_hostname': 'DC-1',
        'system_domain_name': 'WORKGROUP',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'authenticated_username': 'ual\\dc-1$',
        'client_name': None,
        'data_type': 'windows:user_access_logging:clients',
        'role_identifier': '{ad495fc3-0eaa-413d-ba7d-8b13fa7ec598}',
        'role_name': 'Active Directory Domain Services',
        'source_ip_address': '::1',
        'tenant_identifier': '{3facd7dc-85cc-495b-823f-6c96a9e1c40c}',
        'total_accesses': 62,
        'timestamp_desc': definitions.TIME_DESCRIPTION_FIRST_ACCESS}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:user_access_logging:role_access',
        'role_identifier': '{10a9226f-50ee-49d8-a393-9a501d47ce04}',
        'role_name': 'File Server',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FIRST_ACCESS}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'authenticated_username': 'ual\\hunter',
        'client_name': None,
        'data_type': 'windows:user_access_logging:clients',
        'role_identifier': '{10a9226f-50ee-49d8-a393-9a501d47ce04}',
        'role_name': 'File Server',
        'source_ip_address': '10.0.11.10',
        'tenant_identifier': '{00000000-0000-0000-0000-000000000000}',
        'total_accesses': 2,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[30], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:user_access_logging:dns',
        'hostname': 'dc-1',
        'ip_address': '10.0.10.10',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_SEEN}

    self.CheckEventValues(storage_writer, events[38], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:user_access_logging:dns',
        'hostname': 'XTOF-WKS',
        'ip_address': '10.0.11.10',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_SEEN}

    self.CheckEventValues(storage_writer, events[41], expected_event_values)

  def testConvertGUIDToString(self):
    """Tests GUID to string conversion."""
    plugin = user_access_logging.UserAccessLoggingESEDBPlugin()

    guid_string = plugin._ConvertGUIDToString(self._GUID_BYTES)
    self.assertEqual(guid_string, '{35918bc9-196d-40ea-9779-889d79b753f0}')


if __name__ == '__main__':
  unittest.main()
