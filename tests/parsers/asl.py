#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Apple System Log file parser."""

import unittest

from plaso.formatters import asl  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import asl

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ASLParserTest(test_lib.ParserTestCase):
  """Tests for Apple System Log file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'applesystemlog.asl'])
  def testParse(self):
    """Tests the Parse function."""
    parser = asl.ASLParser()
    storage_writer = self._ParseFile(
        [u'applesystemlog.asl'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-25 09:45:35.705481')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.record_position, 442)
    self.assertEqual(event.message_id, 101406)
    self.assertEqual(event.computer_name, u'DarkTemplar-2.local')
    self.assertEqual(event.sender, u'locationd')
    self.assertEqual(event.facility, u'com.apple.locationd')
    self.assertEqual(event.pid, 69)
    self.assertEqual(event.user_sid, u'205')
    self.assertEqual(event.group_id, 205)
    self.assertEqual(event.read_uid, 205)
    self.assertEqual(event.read_gid, 0xffffffff)
    self.assertEqual(event.level, 4)

    # Note that "compatiblity" is spelt incorrectly in the actual message being
    # tested here.
    expected_message = (
        u'Incorrect NSStringEncoding value 0x8000100 detected. '
        u'Assuming NSASCIIStringEncoding. Will stop this compatiblity '
        u'mapping behavior in the near future.')

    self.assertEqual(event.message, expected_message)

    expected_extra = (
        u'CFLog Local Time: 2013-11-25 09:45:35.701, '
        u'CFLog Thread: 1007, '
        u'Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51')

    self.assertEqual(event.extra_information, expected_extra)

    expected_message = (
        u'MessageID: 101406 '
        u'Level: WARNING (4) '
        u'User ID: 205 '
        u'Group ID: 205 '
        u'Read User: 205 '
        u'Read Group: ALL '
        u'Host: DarkTemplar-2.local '
        u'Sender: locationd '
        u'Facility: com.apple.locationd '
        u'Message: {0:s} {1:s}').format(expected_message, expected_extra)

    expected_short_message = (
        u'Sender: locationd '
        u'Facility: com.apple.locationd')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
