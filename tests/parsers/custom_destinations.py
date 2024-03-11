#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the .customDestinations-ms file parser."""

import unittest

from plaso.parsers import custom_destinations

from tests.parsers import test_lib


class CustomDestinationsParserTest(test_lib.ParserTestCase):
  """Tests for the .customDestinations-ms file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = custom_destinations.CustomDestinationsParser()
    storage_writer = self._ParseFile(
        ['custom_destinations', '5afe4de1b92fc382.customDestinations-ms'],
        parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 45)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test shortcut event data.
    expected_event_values = {
        'access_time': '2009-07-13T23:55:56.2481035+00:00',
        'command_line_arguments': (
            '{DE3895CB-077B-4C38-B6E3-F3DE1E0D84FC} %systemroot%\\\\'
            'system32\\\\control.exe /name Microsoft.Display'),
        'creation_time': '2009-07-13T23:55:56.2481035+00:00',
        'data_type': 'windows:lnk:link',
        'description': '@%systemroot%\\\\system32\\\\oobefldr.dll,-1262',
        'drive_serial_number': 0x24ba718b,
        'drive_type': 3,
        'env_var_location': '%SystemRoot%\\\\system32\\\\GettingStarted.exe',
        'file_attribute_flags': 0x00000020,
        'file_size': 11776,
        'icon_location': '%systemroot%\\\\system32\\\\display.dll',
        'link_target': (
            '<My Computer> C:\\\\Windows\\\\System32\\\\GettingStarted.exe'),
        'local_path': 'C:\\\\Windows\\\\System32\\\\GettingStarted.exe',
        'modification_time': '2009-07-14T01:39:11.3880000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 43)
    self.CheckEventData(event_data, expected_event_values)

    # Test distributed link tracking event data.
    expected_event_values = {
        'creation_time': '2010-11-10T19:08:32.6562596+00:00',
        'data_type': 'windows:distributed_link_tracking:creation',
        'mac_address': '00:0c:29:03:1e:1e',
        'origin': '5afe4de1b92fc382.customDestinations-ms',
        'uuid': 'e9215b24-ecfd-11df-a81c-000c29031e1e'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Test shell item event data.
    expected_event_values = {
        'access_time': '2010-11-10T07:41:04+00:00',
        'creation_time': '2009-07-14T03:20:12+00:00',
        'data_type': 'windows:shell_item:file_entry',
        'file_reference': '2331-1',
        'long_name': 'System32',
        'modification_time': '2010-11-10T07:41:04+00:00',
        'name': 'System32',
        'origin': '5afe4de1b92fc382.customDestinations-ms',
        'shell_item_path': '<My Computer> C:\\\\Windows\\\\System32'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 41)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithEmpty(self):
    """Tests the Parse function with an empty jump list."""
    parser = custom_destinations.CustomDestinationsParser()
    storage_writer = self._ParseFile(
        ['custom_destinations', 'c98dce577f884ef8.customDestinations-ms'],
        parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithComplex(self):
    """Tests the Parse function with a complex jump list."""
    parser = custom_destinations.CustomDestinationsParser()
    storage_writer = self._ParseFile(
        ['custom_destinations', '368d807282ccde9d.customDestinations-ms'],
        parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2024-01-16T06:12:42+00:00',
        'creation_time': '2023-07-12T18:11:20+00:00',
        'data_type': 'windows:shell_item:file_entry',
        'file_reference': '407354-78',
        'long_name': 'test',
        'modification_time': '2023-07-14T04:04:02+00:00',
        'name': 'test',
        'origin': '368d807282ccde9d.customDestinations-ms',
        'shell_item_path': '<My Computer> C:\\\\test'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'access_time': '2024-01-16T06:12:41.2400523+00:00',
        'command_line_arguments': 'My Arguments',
        'creation_time': '2023-07-12T18:11:18.2749654+00:00',
        'data_type': 'windows:lnk:link',
        'description': None,
        'drive_serial_number': 0x2ca3d1ae,
        'drive_type': 3,
        'env_var_location': None,
        'file_attribute_flags': 0x00000010,
        'file_size': 4096,
        'icon_location': 'My Icon',
        'link_target': '<My Computer> C:\\\\test',
        'local_path': 'C:\\\\test',
        'modification_time': '2023-07-14T04:04:00.3349887+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'creation_time': '2023-07-12T18:06:36.6282931+00:00',
        'data_type': 'windows:distributed_link_tracking:creation',
        'mac_address': '52:54:00:ee:b6:05',
        'origin': '368d807282ccde9d.customDestinations-ms',
        'uuid': 'd78dbcb3-20de-11ee-a2f8-525400eeb605'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
