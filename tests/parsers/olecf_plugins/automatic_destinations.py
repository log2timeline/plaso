#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the .automaticDestinations-ms OLECF parser plugin."""

import unittest

from plaso.lib import definitions
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 88)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check a AutomaticDestinationsDestListEntryEvent.
    expected_event_values = {
        'birth_droid_file_identifier': '{63eea867-7b85-11e1-8950-005056a50b40}',
        'birth_droid_volume_identifier': (
            '{cf6619c2-66a8-44a6-8849-1582fcd3a338}'),
        'data_type': 'olecf:dest_list:entry',
        'date_time': '2012-04-01 13:52:38.9975382',
        'droid_file_identifier': '{63eea867-7b85-11e1-8950-005056a50b40}',
        'droid_volume_identifier': '{cf6619c2-66a8-44a6-8849-1582fcd3a338}',
        'entry_number': 11,
        'hostname': 'wks-win764bitb',
        'offset': 32,
        'path': 'C:\\Users\\nfury\\Pictures\\The SHIELD',
        'pin_status': -1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    # Check a WinLnkLinkEvent.
    expected_event_values = {
        'data_type': 'windows:lnk:link',
        'date_time': '2010-11-10 07:51:16.7491250',
        'drive_serial_number': 0x24ba718b,
        'drive_type': 3,
        'file_attribute_flags': 0x00002020,
        'file_size': 3545,
        'link_target': '<Users Libraries> <UNKNOWN: 0x00>',
        'local_path': (
            'C:\\Users\\nfury\\AppData\\Roaming\\Microsoft\\Windows\\'
            'Libraries\\Documents.library-ms')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Check a WindowsDistributedLinkTrackingCreationEvent.
    expected_event_values = {
        'data_type': 'windows:distributed_link_tracking:creation',
        'date_time': '2012-03-31 23:01:03.5277415',
        'mac_address': '00:50:56:a5:0b:40',
        'origin': 'DestList entry at offset: 0x00000020',
        'uuid': '63eea867-7b85-11e1-8950-005056a50b40'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

  def testProcessVersion3(self):
    """Tests the Process function on version 3 .automaticDestinations-ms."""
    plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        ['9d1f905ce5044aee.automaticDestinations-ms'], plugin)

    # Number of events:
    # olecf:dest_list:entry: 2
    # windows:lnk:link 2

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check a AutomaticDestinationsDestListEntryEvent.
    expected_event_values = {
        'birth_droid_file_identifier': '{00000000-0000-0000-0000-000000000000}',
        'birth_droid_volume_identifier': (
            '{00000000-0000-0000-0000-000000000000}'),
        'data_type': 'olecf:dest_list:entry',
        'date_time': '2016-01-17 13:08:08.2475045',
        'droid_file_identifier': '{00000000-0000-0000-0000-000000000000}',
        'droid_volume_identifier': '{00000000-0000-0000-0000-000000000000}',
        'entry_number': 2,
        'offset': 32,
        'path': 'http://support.microsoft.com/kb/3124263',
        'pin_status': -1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Check a WinLnkLinkEvent.
    expected_event_values = {
        'data_type': 'windows:lnk:link',
        'date_time': 'Not set',
        'timestamp_desc': definitions.TIME_DESCRIPTION_NOT_A_TIME}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
