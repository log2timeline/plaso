#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the .customDestinations-ms file parser."""

import unittest

from plaso.formatters import winlnk  # pylint: disable=unused-import
from plaso.lib import eventdata
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
    parser_object = custom_destinations.CustomDestinationsParser()
    storage_writer = self._ParseFile(
        [u'5afe4de1b92fc382.customDestinations-ms'], parser_object)

    self.assertEqual(len(storage_writer.events), 126)

    # A shortcut event object.
    # The last accessed timestamp.
    event_object = storage_writer.events[121]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:55:56.248103')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The creation timestamp.
    event_object = storage_writer.events[122]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:55:56.248103')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The last modification timestamp.
    event_object = storage_writer.events[123]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 01:39:11.388000')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
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

    expected_msg_short = (
        u'[@%systemroot%\\system32\\oobefldr.dll,-1262] '
        u'C:\\Windows\\System32\\GettingStarte...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # A shell item event object.
    event_object = storage_writer.events[18]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:41:04')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Name: System32 '
        u'Long name: System32 '
        u'NTFS file reference: 2331-1 '
        u'Shell item path: <My Computer> C:\\Windows\\System32 '
        u'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_msg_short = (
        u'Name: System32 '
        u'NTFS file reference: 2331-1 '
        u'Origin: 5afe4de1b92fc382.customDes...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # A distributed link tracking event object.
    event_object = storage_writer.events[12]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 19:08:32.656259')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'e9215b24-ecfd-11df-a81c-000c29031e1e '
        u'MAC address: 00:0c:29:03:1e:1e '
        u'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_msg_short = (
        u'e9215b24-ecfd-11df-a81c-000c29031e1e '
        u'Origin: 5afe4de1b92fc382.customDestinati...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
