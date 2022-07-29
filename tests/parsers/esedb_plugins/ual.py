# -*- coding: utf-8 -*-
"""Tests for the User Access Logging (UAL) ESE database file."""

import unittest

from plaso.lib import definitions
from plaso.parsers.esedb_plugins import ual

from tests.parsers.esedb_plugins import test_lib


class UserAccessLoggingESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the User Access Logging (UAL) ESE Database plugin."""
  def testProcessDatabase(self):
    """Tests processing the database"""
    plugin = ual.UserAccessLoggingESEDBPlugin()
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
      'os_build_number': 17763,
      'system_dns_hostname': 'DC-1',
      'system_domain_name': 'WORKGROUP',
      'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION
    }

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
      'address': '::1',
      'authenticated_username': 'ual\\dc-1$',
      'client_name': None,
      'days': [0 if i != 197 else 62 for i in range(1,367) ],
      'role_guid': '{AD495FC3-0EAA-413D-BA7D-8B13FA7EC598}',
      'role_name': 'Active Directory Domain Services',
      'tenant_id': '{3FACD7DC-85CC-495B-823F-6C96A9E1C40C}',
      'total_accesses': 62,
      'timestamp_desc': definitions.TIME_DESCRIPTION_FIRST_ACCESS
    }

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
      'role_guid': '{10A9226F-50EE-49D8-A393-9A501D47CE04}',
      'role_name': 'File Server',
      'timestamp_desc': definitions.TIME_DESCRIPTION_FIRST_ACCESS
    }

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
      'address': '10.0.11.10',
      'authenticated_username': 'ual\\hunter',
      'client_name': None,
      'days': [0 if i != 197 else 2 for i in range(1,367) ],
      'role_guid': '{10A9226F-50EE-49D8-A393-9A501D47CE04}',
      'role_name': 'File Server',
      'tenant_id': '{00000000-0000-0000-0000-000000000000}',
      'total_accesses': 2,
      'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS
    }

    self.CheckEventValues(storage_writer, events[30], expected_event_values)

    expected_event_values = {
      'address': '10.0.10.10',
      'hostname': 'dc-1',
      'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_SEEN
    }

    self.CheckEventValues(storage_writer, events[38], expected_event_values)

    expected_event_values = {
      'address': '10.0.11.10',
      'hostname': 'XTOF-WKS',
      'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_SEEN
    }

    self.CheckEventValues(storage_writer, events[41], expected_event_values)


  def testConvertGUIDBytesToString(self):
    """Tests GUID bytes to string conversion."""
    plugin = ual.UserAccessLoggingESEDBPlugin()
    guid = bytes.fromhex(
        'C9 8B 91 35 6D 19 EA 40 97 79 88 9D 79 B7 53 F0')

    # pylint: disable=protected-access
    guid_string = plugin._ConvertGUIDBytesToString(guid)
    expected_guid_string = '{35918BC9-196D-40EA-9779-889D79B753F0}'
    self.assertEqual(guid_string, expected_guid_string)

if __name__ == '__main__':
  unittest.main()
