#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

import io
import sys
import unittest

from plaso.cli import test_lib
from plaso.cli import tools
from plaso.frontend import frontend
from tools import pinfo


class PinfoToolTest(test_lib.CLIToolTestCase):
  """Tests for the pinfo CLI tool."""

  def testPrintStorageInformation(self):
    """Tests the PrintStorageInformation function."""
    original_stdout = sys.stdout

    # Make sure the test outputs UTF-8.
    output_writer = tools.StdoutOutputWriter(encoding=u'utf-8')
    test_tool = pinfo.PinfoTool(output_writer=output_writer)

    options = frontend.Options()
    options.storage_file = self._GetTestFilePath([u'psort_test.out'])

    test_tool.ParseOptions(options)

    sys.stdout = io.BytesIO()
    test_tool.PrintStorageInformation()

    # TODO: clean up output so that u'...' is not generated.
    expected_output = (
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\t\tPlaso Storage Information\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'Storage file:\t\t{0:s}\n'
        b'Source processed:\tsyslog\nTime of processing:\t'
        b'2014-02-15T04:33:16+00:00\n'
        b'\n'
        b'Collection information:\n'
        b'\tparser_selection = \n'
        b'\tos_detected = N/A\n'
        b'\tconfigured_zone = UTC\n'
        b'\tdebug = False\n'
        b'\tparsers = [u\'sqlite\', u\'winfirewall\', u\'selinux\', '
        b'u\'recycle_bin\', u\'filestat\', u\'syslog\', u\'lnk\', '
        b'u\'xchatscrollback\', u\'symantec_scanlog\', u\'recycle_bin_info2\', '
        b'u\'winevtx\', u\'plist\', u\'bsm_log\', u\'mac_keychain\', '
        b'u\'mac_securityd\', u\'utmp\', u\'asl_log\', u\'opera_global\', '
        b'u\'winjob\', u\'prefetch\', u\'winreg\', u\'msiecf\', u\'bencode\', '
        b'u\'skydrive_log\', u\'openxml\', u\'utmpx\', u\'winevt\', '
        b'u\'hachoir\', u\'opera_typed_history\', u\'mac_appfirewall_log\', '
        b'u\'olecf\', u\'xchatlog\', u\'macwifi\', u\'mactime\', '
        b'u\'java_idx\', u\'mcafee_protection\', u\'skydrive_log_error\']\n'
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
        b'\tCounter: total = 15\n'
        b'\tCounter: syslog = 12\n'
        b'\tCounter: filestat = 3\n'
        b'\n'
        b'Store information:\n'
        b'\tNumber of available stores: 7\n'
        b'\tStore information details omitted (to see use: --verbose)\n'
        b'\n'
        b'Preprocessing information omitted (to see use: --verbose).\n'
        b'\n'
        b'No reports stored.\n'
        b'-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+'
        b'-+-+-+-+-+-+').format(options.storage_file.encode(u'utf-8'))

    output = sys.stdout.getvalue()

    self.assertEqual(output, expected_output)

    sys.stdout = original_stdout


if __name__ == '__main__':
  unittest.main()
