#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the .customDestinations-ms file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winlnk  # pylint: disable=unused-import
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
    event = events[121]

    self.CheckTimestamp(event.timestamp, '2009-07-13 23:55:56.248104')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    # The creation timestamp.
    event = events[122]

    self.CheckTimestamp(event.timestamp, '2009-07-13 23:55:56.248104')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    # The last modification timestamp.
    event = events[123]

    self.CheckTimestamp(event.timestamp, '2009-07-14 01:39:11.388000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

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

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # A shell item event.
    event = events[18]

    self.CheckTimestamp(event.timestamp, '2010-11-10 07:41:04.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

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

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # A distributed link tracking event.
    event = events[12]

    self.CheckTimestamp(event.timestamp, '2010-11-10 19:08:32.656260')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'e9215b24-ecfd-11df-a81c-000c29031e1e '
        'MAC address: 00:0c:29:03:1e:1e '
        'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_short_message = (
        'e9215b24-ecfd-11df-a81c-000c29031e1e '
        'Origin: 5afe4de1b92fc382.customDestinati...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
