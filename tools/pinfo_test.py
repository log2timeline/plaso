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
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.storage_file = test_file

    self._test_tool.ParseOptions(options)

    self._test_tool.PrintStorageInformation()

    expected_parsers = u', '.join(sorted([
        u'android_app_usage',
        u'asl_log',
        u'bencode',
        u'binary_cookies',
        u'bsm_log',
        u'chrome_cache',
        u'chrome_preferences',
        u'cups_ipp',
        u'custom_destinations',
        u'dockerjson',
        u'esedb',
        u'filestat',
        u'firefox_cache',
        u'firefox_cache2',
        u'hachoir',
        u'java_idx',
        u'lnk',
        u'mac_appfirewall_log',
        u'mac_keychain',
        u'mac_securityd',
        u'mactime',
        u'macwifi',
        u'mcafee_protection',
        u'mft',
        u'msiecf',
        u'olecf',
        u'openxml',
        u'opera_global',
        u'opera_typed_history',
        u'pe',
        u'plist',
        u'pls_recall',
        u'popularity_contest',
        u'prefetch',
        u'recycle_bin',
        u'recycle_bin_info2',
        u'rplog',
        u'sccm',
        u'selinux',
        u'skydrive_log',
        u'skydrive_log_old',
        u'sqlite',
        u'symantec_scanlog',
        u'syslog',
        u'usnjrnl',
        u'utmp',
        u'utmpx',
        u'winevt',
        u'winevtx',
        u'winfirewall',
        u'winiis',
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
        b'Serialization format:\tjson\n'
        b'Source processed:\tN/A\n'
        b'Time of processing:\t2016-04-30T06:41:49+00:00\n'
        b'\n'
        b'Collection information:\n'
        b'\tparser_selection = (no list set)\n'
        b'\trecursive = False\n'
        b'\tpreferred_encoding = UTF-8\n'
        b'\tos_detected = N/A\n'
        b'\tconfigured_zone = UTC\n'
        b'\toutput_file = psort_test.json.plaso\n'
        b'\tpreprocess = False\n'
        b'\tversion = 1.4.1_20160414\n'
        b'\tcmd_line = ./tools/log2timeline.py --buffer_size=300 '
        b'psort_test.json.plaso test_data/syslog\n'
        b'\tdebug = False\n'
        b'\truntime = single process mode\n'
        b'\tparsers = {1:s}\n'
        b'\tmethod = OS collection\n'
        b'\tprotobuf_size = 0\n'
        b'\n'
        b'Parser counter information:\n'
        b'\tfilestat = 3\n'
        b'\tsyslog = 13\n'
        b'\tTotal = 16\n'
        b'\n'
        b'Preprocessing information omitted (to see use: --verbose).\n'
        b'\n'
        b'-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+'
        b'-+-+-+-+-+-+\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\t\tPlaso Storage Information\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'Storage file:\t\t{0:s}\n'
        b'Serialization format:\tjson\n'
        b'Source processed:\tN/A\n'
        b'Time of processing:\t2016-04-30T06:41:50+00:00\n'
        b'\n'
        b'Collection information:\n'
        b'\tparser_selection = (no list set)\n'
        b'\trecursive = False\n'
        b'\tpreferred_encoding = UTF-8\n'
        b'\tos_detected = N/A\n'
        b'\tconfigured_zone = Iceland\n'
        b'\toutput_file = psort_test.json.plaso\n'
        b'\tpreprocess = False\n'
        b'\tversion = 1.4.1_20160414\n'
        b'\tcmd_line = ./tools/log2timeline.py -z Iceland '
        b'psort_test.json.plaso test_data/syslog\n'
        b'\tdebug = False\n'
        b'\truntime = single process mode\n'
        b'\tparsers = {1:s}\n'
        b'\tmethod = OS collection\n'
        b'\tprotobuf_size = 0\n'
        b'\n'
        b'Parser counter information:\n'
        b'\tfilestat = 3\n'
        b'\tsyslog = 13\n'
        b'\tTotal = 16\n'
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
