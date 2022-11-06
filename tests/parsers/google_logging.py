#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Google log parser"""

import unittest

from plaso.lib import errors
from plaso.parsers import google_logging

from tests.parsers import test_lib


class GooglelogParserTest(test_lib.ParserTestCase):
  """Tests for the Google logging parser"""

  def testParse(self):
    """Tests the Parse function."""
    parser = google_logging.GoogleLogParser()
    storage_writer = self._ParseFile(['googlelog_test.INFO'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test a single-line log entry.
    expected_event_values = {
        'data_type': 'googlelog:log',
        'file_name': 'logging_functional_test_helper.py',
        'line_number': '65',
        'message': 'This line is log level 0',
        'last_written_time': '0000-12-31T23:59:59.000002'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Test a multi-line log entry.
    expected_event_values = {
        'data_type': 'googlelog:log',
        'message': 'Interesting Stuff\n    that spans two lines',
        'last_written_time': '0000-12-31T23:59:59.000003'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testRaisesUnableToParseForInvalidFiles(self):
    """Test that attempting to parse an invalid file should raise an error."""
    parser = google_logging.GoogleLogParser()

    invalid_file_name = 'apache_access.log'
    invalid_file_path = self._GetTestFilePath([invalid_file_name])
    self._SkipIfPathNotExists(invalid_file_path)

    with self.assertRaises(errors.WrongParser):
      self._ParseFile([invalid_file_name], parser)


if __name__ == '__main__':
  unittest.main()
