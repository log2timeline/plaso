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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 126)

    events = list(storage_writer.GetEvents())

    # A shortcut event.
    # The last accessed timestamp.
    expected_event_values = {
        'timestamp': '2009-07-13 23:55:56.248104',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[121], expected_event_values)

    # The creation timestamp.
    expected_event_values = {
        'timestamp': '2009-07-13 23:55:56.248104',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[122], expected_event_values)

    # The last modification timestamp.
    expected_event_values = {
        'timestamp': '2009-07-14 01:39:11.388000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[123], expected_event_values)

    expected_message = (
        '[@%systemroot%\\system32\\oobefldr.dll,-1262] '
        'File size: 11776 '
        'File attribute flags: 0x00000020 '
        'Drive type: 3 '
        'Drive serial number: 0x24ba718b '
        'Local path: C:\\Windows\\System32\\GettingStarted.exe '
        'cmd arguments: {DE3895CB-077B-4C38-B6E3-F3DE1E0D84FC} '
        '%systemroot%\\system32\\control.exe /name Microsoft.Display '
        'env location: %SystemRoot%\\system32\\GettingStarted.exe '
        'Icon location: %systemroot%\\system32\\display.dll '
        'Link target: <My Computer> C:\\Windows\\System32\\GettingStarted.exe')

    expected_short_message = (
        '[@%systemroot%\\system32\\oobefldr.dll,-1262] '
        'C:\\Windows\\System32\\GettingStarte...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[123])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # A shell item event.
    expected_event_values = {
        'timestamp': '2010-11-10 07:41:04.000000'}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_message = (
        'Name: System32 '
        'Long name: System32 '
        'NTFS file reference: 2331-1 '
        'Shell item path: <My Computer> C:\\Windows\\System32 '
        'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_short_message = (
        'Name: System32 '
        'NTFS file reference: 2331-1 '
        'Origin: 5afe4de1b92fc382.customDes...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[18])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # A distributed link tracking event.
    expected_event_values = {
        'timestamp': '2010-11-10 19:08:32.656260'}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)

    expected_message = (
        'e9215b24-ecfd-11df-a81c-000c29031e1e '
        'MAC address: 00:0c:29:03:1e:1e '
        'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_short_message = (
        'e9215b24-ecfd-11df-a81c-000c29031e1e '
        'Origin: 5afe4de1b92fc382.customDestinati...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[12])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
