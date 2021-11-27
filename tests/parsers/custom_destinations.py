#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the .customDestinations-ms file parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import custom_destinations

from tests.parsers import test_lib


class CustomDestinationsParserTest(test_lib.ParserTestCase):
  """Tests for the .customDestinations-ms file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = custom_destinations.CustomDestinationsParser()
    storage_writer = self._ParseFile(
        ['5afe4de1b92fc382.customDestinations-ms'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 126)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # The shortcut last accessed event.
    expected_event_values = {
        'data_type': 'windows:lnk:link',
        'date_time': '2009-07-13 23:55:56.2481035',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[121], expected_event_values)

    # The shortcut creation event.
    expected_event_values = {
        'data_type': 'windows:lnk:link',
        'date_time': '2009-07-13 23:55:56.2481035',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[122], expected_event_values)

    # The shortcut last modification event.
    expected_event_values = {
        'command_line_arguments': (
            '{DE3895CB-077B-4C38-B6E3-F3DE1E0D84FC} %systemroot%\\system32\\'
            'control.exe /name Microsoft.Display'),
        'data_type': 'windows:lnk:link',
        'date_time': '2009-07-14 01:39:11.3880000',
        'description': '@%systemroot%\\system32\\oobefldr.dll,-1262',
        'drive_serial_number': 0x24ba718b,
        'drive_type': 3,
        'env_var_location': '%SystemRoot%\\system32\\GettingStarted.exe',
        'file_attribute_flags': 0x00000020,
        'file_size': 11776,
        'icon_location': '%systemroot%\\system32\\display.dll',
        'link_target': (
            '<My Computer> C:\\Windows\\System32\\GettingStarted.exe'),
        'local_path': 'C:\\Windows\\System32\\GettingStarted.exe',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[123], expected_event_values)

    # A shell item event.
    expected_event_values = {
        'data_type': 'windows:shell_item:file_entry',
        'date_time': '2010-11-10 07:41:04',
        'file_reference': '2331-1',
        'long_name': 'System32',
        'name': 'System32',
        'origin': '5afe4de1b92fc382.customDestinations-ms',
        'shell_item_path': '<My Computer> C:\\Windows\\System32'}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    # A distributed link tracking event.
    expected_event_values = {
        'data_type': 'windows:distributed_link_tracking:creation',
        'date_time': '2010-11-10 19:08:32.6562596',
        'mac_address': '00:0c:29:03:1e:1e',
        'origin': '5afe4de1b92fc382.customDestinations-ms',
        'uuid': 'e9215b24-ecfd-11df-a81c-000c29031e1e'}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)


if __name__ == '__main__':
  unittest.main()
