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
    """Tests the parse function on an example file."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['googlelog_test.INFO'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetSortedEvents())

    # Test a regular event.
    expected_event_values = {
        'data_type': 'googlelog:log',
        'file_name': 'logging_functional_test_helper.py',
        'line_number': '65',
        'message': 'This line is log level 0',
        'timestamp': '2019-12-31 23:59:59.000002'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Test a multiline event.
    expected_event_values = {
        'data_type': 'googlelog:log',
        'message': 'Interesting Stuff\n    that spans two lines'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

  def testRaisesUnableToParseForInvalidFiles(self):
    """Test that attempting to parse an invalid file should raise an error."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}

    invalid_file_name = 'access.log'
    invalid_file_path = self._GetTestFilePath([invalid_file_name])
    self._SkipIfPathNotExists(invalid_file_path)

    with self.assertRaises(errors.UnableToParseFile):
      self._ParseFile(
          [invalid_file_name], parser,
          knowledge_base_values=knowledge_base_values)


if __name__ == '__main__':
  unittest.main()
