#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Google log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import google_logging

from tests.parsers.text_plugins import test_lib


class GooglelogParserTest(test_lib.TextPluginTestCase):
  """Tests for the Google logging text parser plugin."""

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
