#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the TLN output class."""

from __future__ import unicode_literals

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import tln

from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TLNOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the TLN output module."""

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:output',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
       'pathspec': path_spec_factory.Factory.NewPathSpec(
           dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
           location='/var/log/syslog.1', parent=_OS_PATH_SPEC),
       'text': (
           'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'root'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._output_writer = cli_test_lib.TestOutputWriter()
    output_mediator = self._CreateOutputMediator()
    self._output_module = tln.TLNOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = 'Time|Source|Host|User|Description\n'

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    self._output_module.WriteEventBody(event, event_data, None)

    expected_event_body = (
        '1340821021|LOG|ubuntu|root|2012-06-27T18:17:01+00:00; Unknown Time; '
        'Reporter <CRON> PID:  8442  (pam_unix(cron:session): '
        'session closed for user root)\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count('|'), 4)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)


class L2TTLNOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the log2timeline TLN output module."""

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:output',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
       'pathspec': path_spec_factory.Factory.NewPathSpec(
           dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
           location='/var/log/syslog.1', parent=_OS_PATH_SPEC),
       'text': (
           'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'root'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = tln.L2TTLNOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = 'Time|Source|Host|User|Description|TZ|Notes\n'

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    self._output_module.WriteEventBody(event, event_data, None)

    expected_event_body = (
        '1340821021|LOG|ubuntu|root|2012-06-27T18:17:01+00:00; Unknown Time; '
        'Reporter <CRON> PID:  8442  (pam_unix(cron:session): '
        'session closed for user root)'
        '|UTC|File: OS: /var/log/syslog.1 inode: 12345678\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count('|'), 6)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)


if __name__ == '__main__':
  unittest.main()
