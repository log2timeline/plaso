#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Apple System Log file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import asl as _  # pylint: disable=unused-import
from plaso.parsers import asl

from tests.parsers import test_lib


class ASLParserTest(test_lib.ParserTestCase):
  """Tests for Apple System Log file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = asl.ASLParser()
    storage_writer = self._ParseFile(['applesystemlog.asl'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-25 09:45:35.705481')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.record_position, 442)
    self.assertEqual(event_data.message_id, 101406)
    self.assertEqual(event_data.computer_name, 'DarkTemplar-2.local')
    self.assertEqual(event_data.sender, 'locationd')
    self.assertEqual(event_data.facility, 'com.apple.locationd')
    self.assertEqual(event_data.pid, 69)
    self.assertEqual(event_data.user_sid, '205')
    self.assertEqual(event_data.group_id, 205)
    self.assertEqual(event_data.read_uid, 205)
    self.assertEqual(event_data.read_gid, -1)
    self.assertEqual(event_data.level, 4)

    # Note that "compatiblity" is spelt incorrectly in the actual message being
    # tested here.
    expected_message = (
        'Incorrect NSStringEncoding value 0x8000100 detected. '
        'Assuming NSASCIIStringEncoding. Will stop this compatiblity '
        'mapping behavior in the near future.')

    self.assertEqual(event_data.message, expected_message)

    expected_extra = (
        'CFLog Local Time: 2013-11-25 09:45:35.701, '
        'CFLog Thread: 1007, '
        'Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51')

    self.assertEqual(event_data.extra_information, expected_extra)

    expected_message = (
        'MessageID: 101406 '
        'Level: WARNING (4) '
        'User ID: 205 '
        'Group ID: 205 '
        'Read User: 205 '
        'Read Group: ALL '
        'Host: DarkTemplar-2.local '
        'Sender: locationd '
        'Facility: com.apple.locationd '
        'Message: {0:s} {1:s}').format(expected_message, expected_extra)

    expected_short_message = (
        'Sender: locationd '
        'Facility: com.apple.locationd')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
