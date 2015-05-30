#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the "raw" (or native) Python output modulr."""

import unittest

from plaso.cli import test_lib as cli_test_lib
from plaso.output import rawpy
from plaso.output import test_lib


class NativePythonOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the "raw" (or native) Python output module."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = rawpy.NativePythonOutputModule(
        output_mediator, output_writer=self._output_writer)
    self._event_object = test_lib.TestEventObject()

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    self._output_module.WriteEventBody(self._event_object)

    expected_event_body = (
        b'+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-'
        b'+-+-+-+-+-+-\n'
        b'[Timestamp]:\n  2012-06-27T18:17:01+00:00\n[Pathspec]:\n'
        b'  type: OS, location: /cases/image.dd\n'
        b'  type: TSK, inode: 15, location: /var/log/syslog.1\n'
        b'  \n'
        b'\n'
        b'[Reserved attributes]:\n'
        b'  {data_type} test:output\n'
        b'  {display_name} OS: /var/log/syslog.1\n'
        b'  {hostname} ubuntu\n'
        b'  {inode} 12345678\n'
        b'  {timestamp} 1340821021000000\n'
        b'  {username} root\n'
        b'  {uuid} 79028cc28d324634a85533d0fbc49275\n'
        b'\n'
        b'[Additional attributes]:\n'
        b'  {text} Reporter <CRON> PID: |8442| (pam_unix(cron:session): '
        b'session\n'
        b' closed for user root)\n')

    event_body = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(event_body.split(b'\n'), expected_event_body.split(b'\n'))


if __name__ == '__main__':
  unittest.main()
