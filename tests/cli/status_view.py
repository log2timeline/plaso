#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the status view."""

import sys
import unittest

import mock

from dfvfs.lib import definitions as dfvfs_definitions

import plaso

from plaso.cli import status_view
from plaso.engine import processing_status

from tests.cli import test_lib


class StatusViewTest(test_lib.CLIToolTestCase):
  """Tests for the status view."""

  # pylint: disable=protected-access

  def _MockTime(self):
    """Mock function to simulate time.time()

    Returns:
      int: stored time via self._mocked_time"""
    return self._mocked_time

  def setUp(self):
    """Makes preparations before running an individual test."""

    self.mock_time = mock.patch(
        'plaso.cli.status_view.time.time', self._MockTime)
    self._mocked_time = 0
    self.mock_time.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.mock_time.stop()

  def _CheckOutput(self, output, expected_output):
    """Compares the output against the expected output.

    The actual processing time is ignored, since it can vary.

    Args:
      output (str): tool output.
      expected_output (list[str]): expected tool output.
    """
    output = output.split('\n')

    self.assertEqual(output[:4], expected_output[:4])
    self.assertTrue(output[4].startswith('Processing time\t\t: '))
    self.assertEqual(output[5:], expected_output[5:])

  # TODO: add tests for _ClearScreen
  # TODO: add tests for _FormatAnalysisStatusTableRow
  # TODO: add tests for _FormatExtractionStatusTableRow
  # TODO: add tests for _FormatSizeInUnitsOf1024
  # TODO: add tests for _PrintAnalysisStatusHeader
  # TODO: add tests for _PrintAnalysisStatusUpdateLinear
  # TODO: add tests for _PrintAnalysisStatusUpdateWindow
  # TODO: add tests for _PrintEventsStatus

  def testPrintExtractionStatusUpdateLinear(self):
    """Tests the PrintExtractionStatusUpdateLinear function."""
    output_writer = test_lib.TestOutputWriter()

    test_view = status_view.StatusView(output_writer, 'test_tool')
    test_view.SetSourceInformation(
        '/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(
        'f_identifier', 'f_status', 123, 0,
        'f_test_file', 1, 29, 1, 2, 3, 456, 5, 6, 9, 10)
    test_view._PrintExtractionStatusUpdateLinear(process_status)

    expected_output = (
        'Processing time: 00:00:00\n'
        'f_identifier (PID: 123) status: f_status, event data produced: 2, '
        'events produced: 456, file: f_test_file\n'
        '\n')

    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

    process_status.UpdateWorkerStatus(
        'w_identifier', 'w_status', 123, 0,
        'w_test_file', 1, 2, 3, 4, 5, 6, 9, 10, 11, 12)
    test_view._PrintExtractionStatusUpdateLinear(process_status)

    expected_output = (
        'Processing time: 00:00:00\n'
        'f_identifier (PID: 123) status: f_status, event data produced: 2, '
        'events produced: 456, file: f_test_file\n'
        'w_identifier (PID: 123) status: w_status, event data produced: 6, '
        'file: w_test_file\n'
        '\n')

    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testPrintExtractionStatusUpdateWindow(self):
    """Tests the _PrintExtractionStatusUpdateWindow function."""
    output_writer = test_lib.TestOutputWriter()

    test_view = status_view.StatusView(output_writer, 'test_tool')
    test_view.SetSourceInformation(
        '/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(
        'f_identifier', 'f_status', 123, 0,
        'f_test_file', 1, 29, 1, 2, 3, 456, 5, 6, 9, 10)
    test_view._PrintExtractionStatusUpdateWindow(process_status)

    table_header = (
        'Identifier      '
        'PID     '
        'Status          '
        'Memory          '
        'Sources         '
        'Events          '
        'File')

    if not sys.platform.startswith('win'):
      table_header = '\x1b[1m{0:s}\x1b[0m'.format(table_header)

    expected_output = [
        'plaso - test_tool version {0:s}'.format(plaso.__version__),
        '',
        'Source path\t\t: /test/source/path',
        'Source type\t\t: directory',
        'Processing time\t\t: 00:00:00',
        '',
        table_header,
        ('f_identifier    '
         '123     '
         'f_status        '
         '0 B             '
         '29 (29)         '
         '456 (456)       '
         'f_test_file'),
        '',
        '']

    output = output_writer.ReadOutput()
    self._CheckOutput(output, expected_output)

    process_status.UpdateWorkerStatus(
        'w_identifier', 'w_status', 123, 0,
        'w_test_file', 1, 2, 3, 4, 5, 6, 9, 10, 11, 12)
    test_view._PrintExtractionStatusUpdateWindow(process_status)

    table_header = (
        'Identifier      '
        'PID     '
        'Status          '
        'Memory          '
        'Sources         '
        'Event Data      '
        'File')

    if not sys.platform.startswith('win'):
      table_header = '\x1b[1m{0:s}\x1b[0m'.format(table_header)

    expected_output = [
        'plaso - test_tool version {0:s}'.format(plaso.__version__),
        '',
        'Source path\t\t: /test/source/path',
        'Source type\t\t: directory',
        'Processing time\t\t: 00:00:00',
        '',
        table_header,
        ('f_identifier    '
         '123     '
         'f_status        '
         '0 B             '
         '29 (29)         '
         '2 (2)           '
         'f_test_file'),
        ('w_identifier    '
         '123     '
         'w_status        '
         '0 B             '
         '2 (2)           '
         '4 (4)           '
         'w_test_file'),
        '',
        '']

    output = output_writer.ReadOutput()
    self._CheckOutput(output, expected_output)

  def testFormatProcessingTime(self):
    """Tests the _FormatProcessingTime function."""
    output_writer = test_lib.TestOutputWriter()

    process_status = processing_status.ProcessingStatus()

    test_view = status_view.StatusView(output_writer, 'test_tool')
    test_view.SetSourceInformation(
        '/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status.start_time = 0
    processing_time = test_view._FormatProcessingTime(process_status)

    self.assertEqual(processing_time, '00:00:00')

    self._mocked_time = 12 * 60 * 60 + 31 * 60 +15
    processing_time = test_view._FormatProcessingTime(process_status)

    self.assertEqual(processing_time, '12:31:15')

    self._mocked_time = 24 * 60 * 60
    processing_time = test_view._FormatProcessingTime(process_status)

    self.assertEqual(processing_time, '1 day, 00:00:00')

    self._mocked_time = 5 * 24 * 60 * 60 + 5 * 60 * 60 + 61
    processing_time = test_view._FormatProcessingTime(process_status)

    self.assertEqual(processing_time, '5 days, 05:01:01')

  # TODO: add tests for _PrintTasksStatus
  # TODO: add tests for GetAnalysisStatusUpdateCallback
  # TODO: add tests for GetExtractionStatusUpdateCallback
  # TODO: add tests for PrintAnalysisReportsDetails

  def testPrintExtractionStatusHeader(self):
    """Tests the PrintExtractionStatusHeader function."""
    output_writer = test_lib.TestOutputWriter()

    test_view = status_view.StatusView(output_writer, 'test_tool')
    test_view.SetSourceInformation(
        '/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    test_view.PrintExtractionStatusHeader(None)

  # TODO: add tests for PrintExtractionSummary
  # TODO: add tests for SetMode
  # TODO: add tests for SetSourceInformation
  # TODO: add tests for SetStorageFileInformation


if __name__ == '__main__':
  unittest.main()
