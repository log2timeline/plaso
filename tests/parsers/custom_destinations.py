#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the .customDestinations-ms file parser."""

import unittest

from plaso.formatters import winlnk  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import custom_destinations

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class CustomDestinationsParserTest(test_lib.ParserTestCase):
  """Tests for the .customDestinations-ms file parser."""

  @shared_test_lib.skipUnlessHasTestFile([
      u'5afe4de1b92fc382.customDestinations-ms'])
  def testParse(self):
    """Tests the Parse function."""
    parser = custom_destinations.CustomDestinationsParser()
    storage_writer = self._ParseFile(
        [u'5afe4de1b92fc382.customDestinations-ms'], parser)

    self.assertEqual(storage_writer.number_of_events, 126)

    events = list(storage_writer.GetEvents())

    # A shortcut event.
    # The last accessed timestamp.
    event = events[121]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:55:56.248103')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The creation timestamp.
    event = events[122]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:55:56.248103')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The last modification timestamp.
    event = events[123]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 01:39:11.388000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[@%systemroot%\\system32\\oobefldr.dll,-1262] '
        u'File size: 11776 '
        u'File attribute flags: 0x00000020 '
        u'Drive type: 3 '
        u'Drive serial number: 0x24ba718b '
        u'Local path: C:\\Windows\\System32\\GettingStarted.exe '
        u'cmd arguments: {DE3895CB-077B-4C38-B6E3-F3DE1E0D84FC} '
        u'%systemroot%\\system32\\control.exe /name Microsoft.Display '
        u'env location: %SystemRoot%\\system32\\GettingStarted.exe '
        u'Icon location: %systemroot%\\system32\\display.dll '
        u'Link target: <My Computer> C:\\Windows\\System32\\GettingStarted.exe')

    expected_short_message = (
        u'[@%systemroot%\\system32\\oobefldr.dll,-1262] '
        u'C:\\Windows\\System32\\GettingStarte...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # A shell item event.
    event = events[18]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:41:04')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Name: System32 '
        u'Long name: System32 '
        u'NTFS file reference: 2331-1 '
        u'Shell item path: <My Computer> C:\\Windows\\System32 '
        u'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_short_message = (
        u'Name: System32 '
        u'NTFS file reference: 2331-1 '
        u'Origin: 5afe4de1b92fc382.customDes...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # A distributed link tracking event.
    event = events[12]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 19:08:32.656259')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'e9215b24-ecfd-11df-a81c-000c29031e1e '
        u'MAC address: 00:0c:29:03:1e:1e '
        u'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_short_message = (
        u'e9215b24-ecfd-11df-a81c-000c29031e1e '
        u'Origin: 5afe4de1b92fc382.customDestinati...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
