#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Google log parser"""

from __future__ import unicode_literals

import unittest

from plaso.lib import errors
from plaso.parsers import google_logging

from tests.parsers import test_lib


class GooglelogTest(test_lib.ParserTestCase):
  """Tests for the Google logging parser"""

  def testEventsParsed(self):
    """Test that the parser produces events, and the number we expect."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['googlelog_test.INFO'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

  def testFirstEventAsExpected(self):
    """Check that the fields in the first event has the correct values."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['googlelog_test.INFO'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]
    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.priority, 'I')
    self.assertEqual(event_data.line_number, '65')
    self.assertEqual(event_data.file_name, 'logging_functional_test_helper.py')
    self.assertEqual(event_data.message, 'This line is VLOG level 0')

  def testMultilineEventAsExpected(self):
    """Check that an event that spans multiple lines is processed correctly."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['googlelog_test.INFO'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetSortedEvents())

    event = events[2]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    message = event_data.message

    self.assertIn('\n', message)

  def testEventFormatting(self):
    """Test that the events are formatting correctly."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['googlelog_test.INFO'], parser,
        knowledge_base_values=knowledge_base_values)

    events = list(storage_writer.GetSortedEvents())

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2019-12-31 23:59:59.000002')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_string = (
        'logging_functional_test_helper.py: 65] This line is log level 0')
    expected_short = 'This line is log level 0'
    self._TestGetMessageStrings(event_data, expected_string, expected_short)

  def testRaisesUnableToParseForInvalidFiles(self):
    """Test that attempting to parse an invalid file should raise an error."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}

    for invalid_file in ['access.log']:
      with self.assertRaises(errors.UnableToParseFile):
        self._ParseFile(
            [invalid_file], parser, knowledge_base_values=knowledge_base_values)


if __name__ == '__main__':
  unittest.main()
