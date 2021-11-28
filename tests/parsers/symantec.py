#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Symantec AV Log parser."""

import unittest

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'action0': '14',
        'action1': '5',
        'action2': '3',
        'cat': '1',
        'date_time': '2012-11-30 10:47:29',
        'data_type': 'av:symantec:scanlog',
        'event': '5',
        'event_data': '201\t4\t6\t1\t65542\t0\t0\t0\t0\t0\t0',
        'file': 'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt',
        'scanid': '0',
        'user': 'davnads',
        'virus': 'W32.Changeup!gen33'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
