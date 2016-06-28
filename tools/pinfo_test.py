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

  def testCompareStorageInformation(self):
    """Tests the CompareStorageInformation function."""
    test_file1 = self._GetTestFilePath([u'psort_test.json.plaso'])
    test_file2 = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file1

    self._test_tool.ParseOptions(options)

    self.assertTrue(self._test_tool.CompareStorageInformation())

    output = self._output_writer.ReadOutput()
    self.assertEqual(output, b'Storage files are identical.\n')

    options = cli_test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file2

    self._test_tool.ParseOptions(options)

    self.assertFalse(self._test_tool.CompareStorageInformation())

  def testPrintStorageInformation(self):
    """Tests the PrintStorageInformation function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.storage_file = test_file

    self._test_tool.ParseOptions(options)

    self._test_tool.PrintStorageInformation()

    expected_output = (
        b'\n'
        b'************************** Plaso Storage Information ****************'
        b'***********\n'
        b'            Filename : psort_test.json.plaso\n'
        b'      Format version : 20160431\n'
        b'Serialization format : json\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'*********************************** Sessions ************************'
        b'***********\n'
        b'---------------------------------------------------------------------'
        b'-----------\n')

    output = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))


if __name__ == '__main__':
  unittest.main()
