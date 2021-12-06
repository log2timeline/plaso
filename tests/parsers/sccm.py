#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the SCCM Logs Parser."""

import unittest

from plaso.parsers import sccm

from tests.parsers import test_lib


class SCCMLogsUnitTest(test_lib.ParserTestCase):
  """Tests for the SCCM Logs Parser."""

  def testParse(self):
    """Tests for the Parse function."""
    parser = sccm.SCCMParser()
    storage_writer = self._ParseFile(['sccm_various.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # time="19:33:19.766-330" date="11-28-2014"
    expected_event_values = {
        'date_time': '2014-11-28 19:33:19.766',
        'data_type': 'software_management:sccm:log',
        'timestamp': '2014-11-29 01:03:19.766000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test timestamps with seven digits after seconds.
    # time="10:22:50.8422964" date="1-2-2015"
    expected_event_values = {
        'date_time': '2015-01-02 10:22:50.873496',
        'data_type': 'software_management:sccm:log'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Test timestamps with '-' in microseconds.
    expected_event_values = {
        'date_time': '2014-12-28 13:29:43.373',
        'data_type': 'software_management:sccm:log',
        'timestamp': '2014-12-28 18:59:43.373000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    # Test timestamps with '+' in microseconds.
    expected_event_values = {
        'date_time': '2014-11-24 01:52:13.827',
        'data_type': 'software_management:sccm:log',
        'timestamp': '2014-11-23 17:52:13.827000'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    # Test timestamps with 2 digit UTC offset.
    expected_event_values = {
        'date_time': '2014-11-26 04:20:47.594',
        'data_type': 'software_management:sccm:log',
        'timestamp': '2014-11-26 05:20:47.594000'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    # Test component and text.
    expected_event_values = {
        'component': 'ContentAccess',
        'date_time': '2014-12-23 07:03:10.647',
        'data_type': 'software_management:sccm:log',
        'text': (
            'Releasing content request {4EA97AD6-E7E2-4583-92B9-21F532501337}'),
        'timestamp': '2014-12-23 12:33:10.647000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
