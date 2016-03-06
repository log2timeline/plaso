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
    test_file1 = self._GetTestFilePath([u'psort_test.proto.plaso'])
    test_file2 = self._GetTestFilePath([u'pinfo_test.out'])

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
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])

    options = cli_test_lib.TestOptions()
    options.storage_file = test_file

    self._test_tool.ParseOptions(options)

    self._test_tool.PrintStorageInformation()

    expected_parsers = u', '.join(sorted([
        u'asl_log',
        u'bencode',
        u'bsm_log',
        u'filestat',
        u'hachoir',
        u'java_idx',
        u'lnk',
        u'mac_appfirewall_log',
        u'mac_keychain',
        u'mac_securityd',
        u'mactime',
        u'macwifi',
        u'mcafee_protection',
        u'msiecf',
        u'olecf',
        u'openxml',
        u'opera_global',
        u'opera_typed_history',
        u'plist',
        u'prefetch',
        u'recycle_bin',
        u'recycle_bin_info2',
        u'selinux',
        u'skydrive_log',
        u'skydrive_log_error',
        u'sqlite',
        u'symantec_scanlog',
        u'syslog',
        u'utmp',
        u'utmpx',
        u'winevt',
        u'winevtx',
        u'winfirewall',
        u'winjob',
        u'winreg',
        u'xchatlog',
        u'xchatscrollback']))

    expected_output = (
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\t\tPlaso Storage Information\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'Storage file:\t\t{0:s}\n'
        b'Serialization format:\tproto\n'
        b'Source processed:\tsyslog\nTime of processing:\t'
        b'2014-02-15T04:33:16+00:00\n'
        b'\n'
        b'Collection information:\n'
        b'\tparser_selection = \n'
        b'\tos_detected = N/A\n'
        b'\tconfigured_zone = UTC\n'
        b'\tdebug = False\n'
        b'\tparsers = {1:s}\n'
        b'\tprotobuf_size = 300\n'
        b'\tvss parsing = False\n'
        b'\trecursive = False\n'
        b'\tpreferred_encoding = UTF-8\n'
        b'\tworkers = 12\n'
        b'\toutput_file = psort_test.out\n'
        b'\tversion = 1.1.0-dev_20140213\n'
        b'\tcmd_line = /usr/local/bin/log2timeline.py psort_test.out syslog '
        b'--buffer_size=300\n'
        b'\tpreprocess = False\n'
        b'\truntime = multi threaded\n'
        b'\tmethod = OS collection\n'
        b'\n'
        b'Parser counter information:\n'
        b'\tfilestat = 3\n'
        b'\tsyslog = 12\n'
        b'\tTotal = 15\n'
        b'\n'
        b'Preprocessing information omitted (to see use: --verbose).\n'
        b'\n'
        b'No reports stored.\n'
        b'-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+'
        b'-+-+-+-+-+-+\n').format(
            options.storage_file.encode(u'utf-8'),
            expected_parsers.encode(u'utf-8'))

    output = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))


if __name__ == '__main__':
  unittest.main()
