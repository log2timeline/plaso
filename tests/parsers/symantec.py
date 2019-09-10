#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Symantec AV Log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import symantec as _  # pylint: disable=unused-import
from plaso.parsers import symantec

from tests.parsers import test_lib


class SymantecAccessProtectionUnitTest(test_lib.ParserTestCase):
  """Tests for the Symantec AV Log parser."""

  # pylint: disable=protected-access

  def testGetTimeElementsTuple(self):
    """Tests the _GetTimeElementsTuple function."""
    parser = symantec.SymantecParser()

    expected_time_elements_tuple = (2002, 11, 19, 8, 1, 34)
    time_elements_tuple = parser._GetTimeElementsTuple('200A13080122')
    self.assertEqual(time_elements_tuple, expected_time_elements_tuple)

    expected_time_elements_tuple = (2012, 11, 30, 10, 47, 29)
    time_elements_tuple = parser._GetTimeElementsTuple('2A0A1E0A2F1D')
    self.assertEqual(time_elements_tuple, expected_time_elements_tuple)

  def testParse(self):
    """Tests the Parse function."""
    parser = symantec.SymantecParser()
    storage_writer = self._ParseFile(['Symantec.Log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Test the second entry:
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2012-11-30 10:47:29.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.user, 'davnads')
    expected_file = (
        'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt')
    self.assertEqual(event_data.file, expected_file)

    expected_message = (
        'Event Name: GL_EVENT_INFECTION; '
        'Category Name: GL_CAT_INFECTION; '
        'Malware Name: W32.Changeup!gen33; '
        'Malware Path: '
        'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
        'Action0: Unknown; '
        'Action1: Clean virus from file; '
        'Action2: Delete infected file; '
        'Scan ID: 0; '
        'Event Data: 201\t4\t6\t1\t65542\t0\t0\t0\t0\t0\t0')
    expected_short_message = (
        'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
        'W32.Changeup!gen33; '
        'Unknown; ...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
