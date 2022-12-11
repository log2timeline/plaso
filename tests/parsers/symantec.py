#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Symantec AV Log parser."""

import unittest

from plaso.parsers import symantec

from tests.parsers import test_lib


class SymantecAccessProtectionUnitTest(test_lib.ParserTestCase):
  """Tests for the Symantec AV Log parser."""

  # pylint: disable=protected-access

  def testParse(self):
    """Tests the Parse function."""
    parser = symantec.SymantecParser()
    storage_writer = self._ParseFile(['Symantec.Log'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'action0': '14',
        'action1': '5',
        'action2': '3',
        'cat': '1',
        'data_type': 'av:symantec:scanlog',
        'event': '5',
        'event_data': '201\t4\t6\t1\t65542\t0\t0\t0\t0\t0\t0',
        'file': 'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt',
        'last_written_time': '2012-11-30T10:47:29',
        'scanid': '0',
        'user': 'davnads',
        'virus': 'W32.Changeup!gen33'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
