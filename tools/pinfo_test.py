#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

import unittest

from tests.cli import test_lib as cli_test_lib

from tools import pinfo


class PinfoToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the pinfo CLI tool."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = pinfo.PinfoTool(output_writer=self._output_writer)

  def testCompareStorages(self):
    """Tests the CompareStorages function."""
    test_file1 = self._GetTestFilePath([u'psort_test.json.plaso'])
    test_file2 = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file1

    self._test_tool.ParseOptions(options)

    self.assertTrue(self._test_tool.CompareStorages())

    output = self._output_writer.ReadOutput()
    self.assertEqual(output, b'Storages are identical.\n')

    options = cli_test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file2

    self._test_tool.ParseOptions(options)

    self.assertFalse(self._test_tool.CompareStorages())

    output = self._output_writer.ReadOutput()
    self.assertEqual(output, b'Storages are different.\n')

  def testPrintStorageInformation(self):
    """Tests the PrintStorageInformation function."""
    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.storage_file = test_file

    self._test_tool.ParseOptions(options)

    self._test_tool.PrintStorageInformation()

    expected_output = (
        b'\n'
        b'************************** Plaso Storage Information ****************'
        b'***********\n'
        b'            Filename : pinfo_test.json.plaso\n'
        b'      Format version : 20160525\n'
        b'Serialization format : json\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'*********************************** Sessions ************************'
        b'***********\n'
        b'fcd0c74d-403b-4406-8191-0a4ab19a74ee : '
        b'2016-07-10T19:11:10.270444+00:00\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'**************** Session: fcd0c74d-403b-4406-8191-0a4ab19a74ee ******'
        b'***********\n'
        b'                Start time : 2016-07-10T19:11:10.270444+00:00\n'
        b'           Completion time : 2016-07-10T19:11:11.581644+00:00\n'
        b'              Product name : plaso\n'
        b'           Product version : 1.4.1_20160710\n'
        b'    Command line arguments : ./tools/log2timeline.py --partition=all '
        b'--quiet\n'
        b'                             pinfo_test.json.plaso\n'
        b'                             test_data/tsk_volume_system.raw\n'
        b'  Parser filter expression : N/A\n'
        b'Enabled parser and plugins : N/A\n'
        b'        Preferred encoding : UTF-8\n'
        b'                Debug mode : False\n'
        b'               Filter file : N/A\n'
        b'         Filter expression : N/A\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'************************* Events generated per parser ***************'
        b'***********\n'
        b'Parser (plugin) name : Number of events\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'            filestat : 3\n'
        b'               Total : 3\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'No errors stored.\n'
        b'\n'
        b'No analysis reports stored.\n'
        b'\n')

    output = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))


if __name__ == '__main__':
  unittest.main()
