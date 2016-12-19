#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the StatusView tool object."""

import unittest

import plaso
from plaso.cli.status_view_tool import StatusViewTool
from plaso.cli import tools
from plaso.engine import processing_status

from tests.cli import test_lib

class TestStatusViewTool(StatusViewTool):
  """Class that implements a status view for testing."""

  def __init__(self, input_reader=None, output_writer=None):
    super(TestStatusViewTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)

    self._number_of_analysis_reports = 0
    self._source_path = u'/test/source/path'
    self._source_type_string = u'TESTSOURCE'


class StatusViewToolTest(test_lib.CLIToolTestCase):
  """Tests for the StatusView tool object."""

  # pylint: disable=protected-access

  def testPrintStatusUpdate(self):
    """Tests the PrintStatusUpdate function."""
    input_reader = tools.StdinInputReader(encoding=u'ascii')
    output_writer = test_lib.TestOutputWriter()

    status_view_tool = TestStatusViewTool(
        input_reader=input_reader, output_writer=output_writer)

    status_view_tool._PrintStatusHeader()

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(u'f_identifier', u'f_status', 123,
                                       u'f_test_file', 1, 29, 3, 456, 5, 6, 7,
                                       8, 9, 10)
    status_view_tool._PrintStatusUpdate(process_status)

    string = output_writer.ReadOutput()

    expected_string = (
        b'Source path\t: /test/source/path\n'
        b'Source type\t: TESTSOURCE\n'
        b'\n'
        b'plaso -  version {0:s}\n'
        b'\n'
        b'Source path\t: /test/source/path\n'
        b'Source type\t: TESTSOURCE\n'
        b'\n'
        b'\x1b[1mIdentifier\tPID\tStatus\t\tSources\t\tEvents\t\tFile\x1b[0m\n'
        b'f_identifier\t123\tf_status\t29 (29)\t\t456 (456)\tf_test_file\n'
        b'\n'
    ).format(plaso.GetVersion())
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

    process_status.UpdateWorkerStatus(u'w_identifier', u'w_status', 123,
                                      u'w_test_file', 1, 2, 3, 4, 5, 6, 7, 8, 9,
                                      10)
    status_view_tool._PrintStatusUpdate(process_status)
    string = output_writer.ReadOutput()

    expected_string = (
        b'plaso -  version {0:s}\n'
        b'\n'
        b'Source path\t: /test/source/path\n'
        b'Source type\t: TESTSOURCE\n'
        b'\n'
        b'\x1b[1mIdentifier\tPID\tStatus\t\tSources\t\tEvents\t\tFile\x1b[0m\n'
        b'f_identifier\t123\tf_status\t29 (29)\t\t456 (456)\tf_test_file\n'
        b'w_identifier\t123\tw_status\t2 (2)\t\t4 (4)\t\tw_test_file\n'
        b'\n'
    ).format(plaso.GetVersion())
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

  def testPrintStatusUpdateStream(self):
    """Tests the PrintStatusUpdateStream function."""
    input_reader = tools.StdinInputReader(encoding=u'ascii')
    output_writer = test_lib.TestOutputWriter()

    status_view_tool = TestStatusViewTool(
        input_reader=input_reader, output_writer=output_writer)

    status_view_tool._PrintStatusHeader()

    process_status = processing_status.ProcessingStatus()
    process_status.UpdateForemanStatus(u'f_identifier', u'f_status', 123,
                                       u'f_test_file', 1, 29, 3, 456, 5, 6, 7,
                                       8, 9, 10)
    status_view_tool._PrintStatusUpdateStream(process_status)

    string = output_writer.ReadOutput()

    expected_string = (
        b'Source path\t: /test/source/path\n'
        b'Source type\t: TESTSOURCE\n'
        b'\n'
    )
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

    process_status.UpdateWorkerStatus(u'w_identifier', u'w_status', 123,
                                      u'w_test_file', 1, 2, 3, 4, 5, 6, 7, 8, 9,
                                      10)
    status_view_tool._PrintStatusUpdateStream(process_status)
    string = output_writer.ReadOutput()

    expected_string = (u'w_identifier (PID: 123) - events produced: 4 - '
                       u'file: w_test_file - running: True\n')
    self.assertEqual(string, expected_string)


if __name__ == '__main__':
  unittest.main()
