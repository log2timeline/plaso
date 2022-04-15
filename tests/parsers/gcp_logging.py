# -*- coding: utf-8 -*
"""Tests for the GCP log file parser."""

import unittest

from plaso.parsers import gcp_logging

from tests.parsers import test_lib


class GCPLoggingUnitTest(test_lib.ParserTestCase):
  """Tests for the GCP log file parser."""

  def testParseFile(self):
    """Test parsing of a GCP log file."""
    parser = gcp_logging.GCPLogsParser()
    storage_writer = self._ParseFile(['gcp_logging.jsonl'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'timestamp': '2021-10-19 02:57:47.339377',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:57:39.354769',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:55:51.658015',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:55:46.097818',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:43:48.064377',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:42:22.986298',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:42:13.839954',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:05:41.496590',
        'user': 'fakeemailxyz@gmail.com'}
    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-19 02:04:00.272384'}
    self.CheckEventValues(storage_writer, events[8], expected_event_values)


if __name__ == '__main__':
  unittest.main()
