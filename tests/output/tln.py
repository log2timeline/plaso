#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the TLN output class."""

import unittest

from plaso.formatters import manager as formatters_manager
from plaso.output import tln

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class TLNOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the TLN output module."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._output_writer = cli_test_lib.TestOutputWriter()
    output_mediator = self._CreateOutputMediator()
    self._output_module = tln.TLNOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)
    self._event_object = test_lib.TestEventObject()

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = b'Time|Source|Host|User|Description\n'

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    self._output_module.WriteEventBody(self._event_object)

    expected_event_body = (
        b'1340821021|LOG|ubuntu|root|2012-06-27T18:17:01+00:00; UNKNOWN; '
        b'Reporter <CRON> PID:  8442  (pam_unix(cron:session): '
        b'session closed for user root)\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count(b'|'), 4)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)


class L2TTLNOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the log2timeline TLN output module."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = tln.L2TTLNOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)
    self._event_object = test_lib.TestEventObject()

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = b'Time|Source|Host|User|Description|TZ|Notes\n'

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    self._output_module.WriteEventBody(self._event_object)

    expected_event_body = (
        b'1340821021|LOG|ubuntu|root|2012-06-27T18:17:01+00:00; UNKNOWN; '
        b'Reporter <CRON> PID:  8442  (pam_unix(cron:session): '
        b'session closed for user root)'
        b'|UTC|File: OS: /var/log/syslog.1 inode: 12345678\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count(b'|'), 6)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)


if __name__ == '__main__':
  unittest.main()
