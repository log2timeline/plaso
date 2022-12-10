#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Trend Micro AV Log parser."""

import unittest

from plaso.parsers import trendmicroav

from tests.parsers import test_lib


class TrendMicroUnitTest(test_lib.ParserTestCase):
  """Tests for the Trend Micro AV Log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = trendmicroav.OfficeScanVirusDetectionParser()
    storage_writer = self._ParseFile(['pccnt35.log'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'action': 10,
        'data_type': 'av:trendmicro:scan',
        'filename': 'eicar.com_.gstmp',
        'path': 'C:\\temp\\',
        'scan_type': 1,
        'threat': 'Eicar_test_1',
        'written_time': '2018-01-30T14:45:32+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # The third and last log entry has been edited to match the older,
    # documented format for log lines (without a POSIX timestamp).
    expected_event_values = {
        'action': 10,
        'data_type': 'av:trendmicro:scan',
        'filename': 'eicar.com_.gstmp',
        'path': 'C:\\temp\\',
        'scan_type': 1,
        'threat': 'Eicar_test_1',
        'written_time': '2018-01-30T14:46:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testWebReputationParse(self):
    """Tests the Parse function."""
    parser = trendmicroav.OfficeScanWebReputationParser()
    storage_writer = self._ParseFile(['OfcUrlf.log'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application_name': 'C:\\Users\\user\\Downloads\\wget.exe',
        'block_mode': 1,
        'credibility_rating': 1,
        'credibility_score': 49,
        'data_type': 'av:trendmicro:webrep',
        'group_code': '4E',
        'group_name': 'Malware Accomplice',
        'policy_identifier': 1,
        'threshold': 0,
        'url': 'http://www.eicar.org/download/eicar.com',
        'written_time': '2018-01-23T13:17:02+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
