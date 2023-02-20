#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the for bodyfile parser."""

import unittest

from plaso.parsers import wincc

from tests.parsers import test_lib


class WinCCSyslogTest(test_lib.ParserTestCase):
  """Tests for the Wincc sys logs parser."""

  def testParse(self):
    """Tests the Parse function?"""
    parser = wincc.WinCCSysLogParser()
    storage_writer = self._ParseFile(
        ['Logs', 'Program Files (x86)', 'Siemens', 'WinCC', 'diagnose',
         'WinCC_Sys_01.log'], parser)
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2019-05-27T10:10:04.712Z',
        'data_type': 'wincc:sys_log:entry',

    }
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
