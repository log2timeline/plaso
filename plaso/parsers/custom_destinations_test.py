#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the .customDestinations-ms file parser."""

import unittest

from plaso.formatters import winlnk as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import test_lib
from plaso.parsers import custom_destinations


class CustomDestinationsParserTest(test_lib.ParserTestCase):
  """Tests for the .customDestinations-ms file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = custom_destinations.CustomDestinationsParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([
        u'5afe4de1b92fc382.customDestinations-ms'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 108)

    # A shortcut event object.
    # The last accessed timestamp.
    event_object = event_objects[105]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:55:56.248103')
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The creation timestamp.
    event_object = event_objects[106]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:55:56.248103')
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The last modification timestamp.
    event_object = event_objects[107]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 01:39:11.388000')
    self.assertEquals(
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
        u'Link target: [My Computer, C:\\, Windows, System32, '
        u'GettingStarted.exe]')

    expected_msg_short = (
        u'[@%systemroot%\\system32\\oobefldr.dll,-1262] '
        u'C:\\Windows\\System32\\GettingStarte...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # A shell item event object.
    event_object = event_objects[16]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:41:04')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Name: System32 '
        u'Long name: System32 '
        u'NTFS file reference: 2331-1 '
        u'Origin: 5afe4de1b92fc382.customDestinations-ms')

    expected_msg_short = (
        u'Name: System32 '
        u'NTFS file reference: 2331-1 '
        u'Origin: 5afe4de1b92fc382.customDes...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
