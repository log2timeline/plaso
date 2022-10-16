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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

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
        'data_type': 'av:trendmicro:scan',
        'date_time': '2018-01-30T14:45:32+00:00'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # The third and last event has been edited to match the older, documented
    # format for log lines (without a Unix timestamp).
    expected_event_values = {
        'action': 10,
        'data_type': 'av:trendmicro:scan',
        'date_time': '2018-01-30T14:46:00',
        'filename': 'eicar.com_.gstmp',
        'path': 'C:\\temp\\',
        'scan_type': 1,
        'threat': 'Eicar_test_1',
        'timestamp': '2018-01-30 14:46:00.000000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = trendmicroav.OfficeScanVirusDetectionParser()
    storage_writer = self._ParseFile(
        ['pccnt35.log'], parser, time_zone_string='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # The third and last event has been edited to match the older, documented
    # format for log lines (without a Unix timestamp).
    expected_event_values = {
        'action': 10,
        'data_type': 'av:trendmicro:scan',
        'date_time': '2018-01-30T14:46:00',
        'filename': 'eicar.com_.gstmp',
        'path': 'C:\\temp\\',
        'scan_type': 1,
        'threat': 'Eicar_test_1',
        'timestamp': '2018-01-30 13:46:00.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testWebReputationParse(self):
    """Tests the Parse function."""
    parser = trendmicroav.OfficeScanWebReputationParser()
    storage_writer = self._ParseFile(['OfcUrlf.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

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
        'data_type': 'av:trendmicro:webrep',
        'date_time': '2018-01-23T13:16:22+00:00'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'application_name': 'C:\\Users\\user\\Downloads\\wget.exe',
        'block_mode': 1,
        'credibility_rating': 1,
        'credibility_score': 49,
        'data_type': 'av:trendmicro:webrep',
        'date_time': '2018-01-23T13:17:02+00:00',
        'group_code': '4E',
        'group_name': 'Malware Accomplice',
        'policy_identifier': 1,
        'threshold': 0,
        'url': 'http://www.eicar.org/download/eicar.com'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)


if __name__ == '__main__':
  unittest.main()
