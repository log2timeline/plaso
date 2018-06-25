#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the status view."""

from __future__ import unicode_literals

import unittest
import sys

from dfvfs.lib import definitions as dfvfs_definitions

import plaso

from plaso.cli import status_view
from plaso.engine import processing_status

from tests.cli import test_lib


class StatusViewTest(test_lib.CLIToolTestCase):
  """Tests for the status view."""

  # pylint: disable=protected-access

  def _CheckOutput(self, output, expected_output):
    """Compares the output against the expected output.

    The actual processing time is ignored, since it can vary.

    Args:
      output (bytes): tool output.
      expected_output (list[bytes]): expected tool output.
    """
    output = output.split(b'\n')

    self.assertEqual(output[:4], expected_output[:4])
    self.assertTrue(output[4].startswith(b'Processing time\t: '))
    self.assertEqual(output[5:], expected_output[5:])

  # TODO: add tests for _ClearScreen
  # TODO: add tests for _FormatAnalysisStatusTableRow
  # TODO: add tests for _FormatExtractionStatusTableRow
  # TODO: add tests for _FormatSizeInUnitsOf1024
  # TODO: add tests for _PrintAnalysisStatusHeader
  # TODO: add tests for _PrintAnalysisStatusUpdateLinear
  # TODO: add tests for _PrintAnalysisStatusUpdateWindow

  def testPrintExtractionStatusUpdateLinear(self):
    """Tests the PrintExtractionStatusUpdateLinear function."""
    output_writer = test_lib.TestBinaryOutputWriter()

    test_view = status_view.StatusView(output_writer, 'test_tool')
    test_view.SetSourceInformation(
        '/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(
        'f_identifier', 'f_status', 123, 0,
        'f_test_file', 1, 29, 3, 456, 5, 6, 7,
        8, 9, 10)
    test_view._PrintExtractionStatusUpdateLinear(process_status)

    output = output_writer.ReadOutput()
    self.assertEqual(output, b'')

    process_status.UpdateWorkerStatus(
        'w_identifier', 'w_status', 123, 0,
        'w_test_file', 1, 2, 3, 4, 5, 6, 7, 8, 9,
        10)
    test_view._PrintExtractionStatusUpdateLinear(process_status)

    expected_output = (
        'w_identifier (PID: 123) - events produced: 4 - '
        'file: w_test_file - running: True\n')

    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testPrintExtractionStatusUpdateWindow(self):
    """Tests the _PrintExtractionStatusUpdateWindow function."""
    output_writer = test_lib.TestBinaryOutputWriter()

    test_view = status_view.StatusView(output_writer, 'test_tool')
    test_view.SetSourceInformation(
        '/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(
        'f_identifier', 'f_status', 123, 0,
        'f_test_file', 1, 29, 3, 456, 5, 6, 7,
        8, 9, 10)
    test_view._PrintExtractionStatusUpdateWindow(process_status)

    table_header = (
        b'Identifier      '
        b'PID     '
        b'Status          '
        b'Memory          '
        b'Sources         '
        b'Events          '
        b'File')

    if not sys.platform.startswith('win'):
      table_header = b'\x1b[1m{0:s}\x1b[0m'.format(table_header)

    expected_output = [
        b'plaso - test_tool version {0:s}'.format(plaso.__version__),
        b'',
        b'Source path\t: /test/source/path',
        b'Source type\t: directory',
        b'Processing time\t: 00:00:00',
        b'',
        table_header,
        (b'f_identifier    '
         b'123     '
         b'f_status        '
         b'0 B             '
         b'29 (29)         '
         b'456 (456)       '
         b'f_test_file'),
        b'',
        b'']

    output = output_writer.ReadOutput()
    self._CheckOutput(output, expected_output)

    process_status.UpdateWorkerStatus(
        'w_identifier', 'w_status', 123, 0,
        'w_test_file', 1, 2, 3, 4, 5, 6, 7, 8, 9,
        10)
    test_view._PrintExtractionStatusUpdateWindow(process_status)

    expected_output = [
        b'plaso - test_tool version {0:s}'.format(plaso.__version__),
        b'',
        b'Source path\t: /test/source/path',
        b'Source type\t: directory',
        b'Processing time\t: 00:00:00',
        b'',
        table_header,
        (b'f_identifier    '
         b'123     '
         b'f_status        '
         b'0 B             '
         b'29 (29)         '
         b'456 (456)       '
         b'f_test_file'),
        (b'w_identifier    '
         b'123     '
         b'w_status        '
         b'0 B             '
         b'2 (2)           '
         b'4 (4)           '
         b'w_test_file'),
        b'',
        b'']

    output = output_writer.ReadOutput()
    self._CheckOutput(output, expected_output)

  # TODO: add tests for GetAnalysisStatusUpdateCallback
  # TODO: add tests for GetExtractionStatusUpdateCallback
  # TODO: add tests for PrintAnalysisReportsDetails

  def testPrintExtractionStatusHeader(self):
    """Tests the PrintExtractionStatusHeader function."""
    output_writer = test_lib.TestBinaryOutputWriter()

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
