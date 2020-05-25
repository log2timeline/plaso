#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Google log parser"""

from __future__ import unicode_literals

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
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2019-12-31 23:59:59.000002')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_string = (
        'logging_functional_test_helper.py: 65] This line is log level 0')
    expected_short = 'This line is log level 0'
    self._TestGetMessageStrings(event_data, expected_string, expected_short)

   # Test a multiline event.
    multi_line_event = events[2]
    multi_line_event_data = self._GetEventDataOfEvent(
        storage_writer, multi_line_event)
    multi_line_message = multi_line_event_data.message

    self.assertEqual(
        'Interesting Stuff\n    that spans two lines', multi_line_message)

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
