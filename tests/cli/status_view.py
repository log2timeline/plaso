#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the status view."""

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

  # TODO: add tests for _FormatExtractionStatusTableRow.
  # TODO: add tests for _FormatSizeInUnitsOf1024.

  def testPrintExtractionStatusUpdateLinear(self):
    """Tests the PrintExtractionStatusUpdateLinear function."""
    output_writer = test_lib.TestOutputWriter()

    test_view = status_view.StatusView(output_writer, u'test_tool')
    test_view.SetSourceInformation(
        u'/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(
        u'f_identifier', u'f_status', 123, 0,
        u'f_test_file', 1, 29, 3, 456, 5, 6, 7,
        8, 9, 10)
    test_view._PrintExtractionStatusUpdateLinear(process_status)

    string = output_writer.ReadOutput()

    expected_lines = [b'']
    self.assertEqual(string.split(b'\n'), expected_lines)

    process_status.UpdateWorkerStatus(
        u'w_identifier', u'w_status', 123, 0,
        u'w_test_file', 1, 2, 3, 4, 5, 6, 7, 8, 9,
        10)
    test_view._PrintExtractionStatusUpdateLinear(process_status)
    string = output_writer.ReadOutput()

    expected_string = (
        u'w_identifier (PID: 123) - events produced: 4 - '
        u'file: w_test_file - running: True\n')
    self.assertEqual(string, expected_string)

  def testPrintExtractionStatusUpdateWindow(self):
    """Tests the _PrintExtractionStatusUpdateWindow function."""
    output_writer = test_lib.TestOutputWriter()

    test_view = status_view.StatusView(output_writer, u'test_tool')
    test_view.SetSourceInformation(
        u'/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(
        u'f_identifier', u'f_status', 123, 0,
        u'f_test_file', 1, 29, 3, 456, 5, 6, 7,
        8, 9, 10)
    test_view._PrintExtractionStatusUpdateWindow(process_status)

    string = output_writer.ReadOutput()

    table_header = (
        b'Identifier\tPID\tStatus\t\tMemory\t\tSources\t\tEvents\t\tFile')
    if not sys.platform.startswith(u'win'):
      table_header = b'\x1b[1m{0:s}\x1b[0m'.format(table_header)

    expected_lines = [
        b'plaso - test_tool version {0:s}'.format(plaso.__version__),
        b'',
        b'Source path\t: /test/source/path',
        b'Source type\t: directory',
        b'',
        table_header,
        (b'f_identifier\t123\tf_status\t0 B\t\t29 (29)\t\t456 (456)\t'
         b'f_test_file'),
        b'',
        b'']
    self.assertEqual(string.split(b'\n'), expected_lines)

    process_status.UpdateWorkerStatus(
        u'w_identifier', u'w_status', 123, 0,
        u'w_test_file', 1, 2, 3, 4, 5, 6, 7, 8, 9,
        10)
    test_view._PrintExtractionStatusUpdateWindow(process_status)
    string = output_writer.ReadOutput()

    expected_lines = [
        b'plaso - test_tool version {0:s}'.format(plaso.__version__),
        b'',
        b'Source path\t: /test/source/path',
        b'Source type\t: directory',
        b'',
        table_header,
        (b'f_identifier\t123\tf_status\t0 B\t\t29 (29)\t\t456 (456)\t'
         b'f_test_file'),
        b'w_identifier\t123\tw_status\t0 B\t\t2 (2)\t\t4 (4)\t\tw_test_file',
        b'',
        b'']
    self.assertEqual(string.split(b'\n'), expected_lines)

  # TODO: add tests for GetExtractionStatusUpdateCallback.
  # TODO: add tests for PrintAnalysisReportsDetails.

  def testPrintExtractionStatusHeader(self):
    """Tests the PrintExtractionStatusHeader function."""
    output_writer = test_lib.TestOutputWriter()

    test_view = status_view.StatusView(output_writer, u'test_tool')
    test_view.SetSourceInformation(
        u'/test/source/path', dfvfs_definitions.SOURCE_TYPE_DIRECTORY)

    test_view.PrintExtractionStatusHeader()

  # TODO: add tests for SetMode.
  # TODO: add tests for SetSourceInformation.


if __name__ == '__main__':
  unittest.main()
