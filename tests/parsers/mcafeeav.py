#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the McAfee AV Log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mcafeeav as _  # pylint: disable=unused-import
from plaso.parsers import mcafeeav

from tests.parsers import test_lib


class McafeeAccessProtectionUnitTest(test_lib.ParserTestCase):
  """Tests for the McAfee AV Log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = mcafeeav.McafeeAccessProtectionParser()
    storage_writer = self._ParseFile(['AccessProtectionLog.txt'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[10]

    self.CheckTimestamp(event.timestamp, '2013-09-27 14:42:26.000000')

    # TODO: Test that the UTF-8 byte order mark gets removed from
    # the first line.

    # Test this entry:
    # 9/27/2013 2:42:26 PM  Blocked by Access Protection rule
    #   SOMEDOMAIN\someUser C:\Windows\System32\procexp64.exe C:\Program Files
    # (x86)\McAfee\Common Framework\UdaterUI.exe  Common Standard
    # Protection:Prevent termination of McAfee processes  Action blocked :
    # Terminate

    event = events[11]

    self.CheckTimestamp(event.timestamp, '2013-09-27 14:42:39.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.username, 'SOMEDOMAIN\\someUser')
    self.assertEqual(
        event_data.filename, 'C:\\Windows\\System32\\procexp64.exe')

    expected_message = (
        'File Name: C:\\Windows\\System32\\procexp64.exe '
        'User: SOMEDOMAIN\\someUser '
        'C:\\Program Files (x86)\\McAfee\\Common Framework\\Frame'
        'workService.exe '
        'Blocked by Access Protection rule  '
        'Common Standard Protection:Prevent termination of McAfee processes '
        'Action blocked : Terminate')
    expected_short_message = (
        'C:\\Windows\\System32\\procexp64.exe '
        'Action blocked : Terminate')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
