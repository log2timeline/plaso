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

    test_event = events[0]
    self.assertEqual(test_event.priority, 'I')
    self.assertEqual(test_event.line_number, '748')
    self.assertEqual(test_event.file_name, '')
    self.assertEqual(test_event.body, '')

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

    test_event = events[2]

    self.assertNotEqual(test_event.body.find('\n'), -1)
    self.assertNotEqual(test_event.body.find(''), -1)

  def testEventFormatting(self):
    """Test that the events are formatting correctly."""
    parser = google_logging.GoogleLogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['googlelog_test.INFO'], parser,
        knowledge_base_values=knowledge_base_values)

    events = list(storage_writer.GetSortedEvents())

    test_event = events[1]
    expected_string = ()
    expected_short = ''
    self._TestGetMessageStrings(test_event, expected_string, expected_short)

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