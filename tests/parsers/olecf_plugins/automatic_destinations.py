#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the .automaticDestinations-ms OLECF parser plugin."""

import unittest

from plaso.parsers.olecf_plugins import automatic_destinations

from tests.parsers.olecf_plugins import test_lib


class TestAutomaticDestinationsOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the .automaticDestinations-ms OLECF parser plugin."""

  def testProcessVersion1(self):
    """Tests the Process function on version 1 .automaticDestinations-ms."""
    plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        ['1b4dd67f29cb1962.automaticDestinations-ms'], plugin)

    # Number of events:
    # olecf:dest_list:entry: 11
    # windows:lnk:link 33
    # windows:distributed_link_tracking:creation: 44

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 66)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check a AutomaticDestinationsDestListEntryEvent.
    expected_event_values = {
        'birth_droid_file_identifier': '{63eea867-7b85-11e1-8950-005056a50b40}',
        'birth_droid_volume_identifier': (
            '{cf6619c2-66a8-44a6-8849-1582fcd3a338}'),
        'data_type': 'olecf:dest_list:entry',
        'droid_file_identifier': '{63eea867-7b85-11e1-8950-005056a50b40}',
        'droid_volume_identifier': '{cf6619c2-66a8-44a6-8849-1582fcd3a338}',
        'entry_number': 11,
        'hostname': 'wks-win764bitb',
        'modification_time': '2012-04-01T13:52:38.9975382+00:00',
        'offset': 32,
        'path': 'C:\\Users\\nfury\\Pictures\\The SHIELD',
        'pin_status': -1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)

    # Check a WinLnkLinkEvent.
    expected_event_values = {
        'access_time': '2010-11-10T07:51:23.1085000+00:00',
        'creation_time': '2010-11-10T07:51:16.7491250+00:00',
        'data_type': 'windows:lnk:link',
        'drive_serial_number': 0x24ba718b,
        'drive_type': 3,
        'file_attribute_flags': 0x00002020,
        'file_size': 3545,
        'link_target': '<Users Libraries> <UNKNOWN: 0x00>',
        'local_path': (
            'C:\\Users\\nfury\\AppData\\Roaming\\Microsoft\\Windows\\'
            'Libraries\\Documents.library-ms'),
        'modification_time': '2010-11-10T07:51:23.1085000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check a WindowsDistributedLinkTrackingCreationEvent.
    expected_event_values = {
        'creation_time': '2012-03-31T23:01:03.5277415+00:00',
        'data_type': 'windows:distributed_link_tracking:creation',
        'mac_address': '00:50:56:a5:0b:40',
        'origin': 'DestList entry at offset: 0x00000020',
        'uuid': '63eea867-7b85-11e1-8950-005056a50b40'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessVersion3(self):
    """Tests the Process function on version 3 .automaticDestinations-ms."""
    plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        ['9d1f905ce5044aee.automaticDestinations-ms'], plugin)

    # Event data types:
    # olecf:dest_list:entry: 2
    # windows:lnk:link 2

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check a AutomaticDestinationsDestListEntryEvent.
    expected_event_values = {
        'birth_droid_file_identifier': '{00000000-0000-0000-0000-000000000000}',
        'birth_droid_volume_identifier': (
            '{00000000-0000-0000-0000-000000000000}'),
        'data_type': 'olecf:dest_list:entry',
        'droid_file_identifier': '{00000000-0000-0000-0000-000000000000}',
        'droid_volume_identifier': '{00000000-0000-0000-0000-000000000000}',
        'entry_number': 2,
        'hostname': None,
        'modification_time': '2016-01-17T13:08:08.2475045+00:00',
        'offset': 32,
        'path': 'http://support.microsoft.com/kb/3124263',
        'pin_status': -1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Check a WinLnkLinkEvent.
    expected_event_values = {
        'access_time': None,
        'creation_time': None,
        'data_type': 'windows:lnk:link',
        'drive_serial_number': None,
        'drive_type': None,
        'file_attribute_flags': 0,
        'file_size': 0,
        'link_target': '<Internet Explorer (Homepage)> <UNKNOWN: 0x61>',
        'local_path': None,
        'modification_time': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
