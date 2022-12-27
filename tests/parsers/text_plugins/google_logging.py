#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Google log text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import google_logging

from tests.parsers.text_plugins import test_lib


class GooglelogParserTest(test_lib.TextPluginTestCase):
  """Tests for the Google logging text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = google_logging.GoogleLogTextPlugin()

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'Log file created at: 2019/07/18 06:07:40\n'
        b'Running on machine: plasotest1\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = google_logging.GoogleLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['googlelog_test.INFO'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

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


if __name__ == '__main__':
  unittest.main()
