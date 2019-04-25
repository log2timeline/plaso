#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the "raw" (or native) Python output module."""

from __future__ import unicode_literals

import os
import sys
import unittest

from plaso.output import rawpy

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class NativePythonOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the "raw" (or native) Python output module."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = rawpy.NativePythonOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)
    self._event_object = test_lib.TestEventObject()

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    self._output_module.WriteEventBody(self._event_object)

    if sys.platform.startswith('win'):
      # The dict comparison is very picky on Windows hence we
      # have to make sure the drive letter is in the same case.
      expected_os_location = os.path.abspath('\\{0:s}'.format(
          os.path.join('cases', 'image.dd')))
    else:
      expected_os_location = '{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd'))

    expected_event_body = (
        '+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-'
        '+-+-+-+-+-+-\n'
        '[Timestamp]:\n'
        '  2012-06-27T18:17:01+00:00\n'
        '[Pathspec]:\n'
        '  type: OS, location: {0:s}\n'
        '  type: TSK, inode: 15, location: /var/log/syslog.1\n'
        '  \n'
        '\n'
        '[Reserved attributes]:\n'
        '  {{data_type}} test:output\n'
        '  {{display_name}} OS: /var/log/syslog.1\n'
        '  {{hostname}} ubuntu\n'
        '  {{inode}} 12345678\n'
        '  {{timestamp}} 1340821021000000\n'
        '  {{username}} root\n'
        '\n'
        '[Additional attributes]:\n'
        '  {{text}} Reporter <CRON> PID: |8442| (pam_unix(cron:session): '
        'session\n'
        ' closed for user root)\n').format(expected_os_location)

    event_body = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(event_body.split('\n'), expected_event_body.split('\n'))


if __name__ == '__main__':
  unittest.main()
