#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON output module."""

from __future__ import unicode_literals

import json
import os
import sys
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import json_out

from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class JSONOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the JSON output module."""

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
    self._output_module = json_out.JSONOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = '{'

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteFooter(self):
    """Tests the WriteFooter function."""
    expected_footer = '}'

    self._output_module.WriteFooter()

    footer = self._output_writer.ReadOutput()
    self.assertEqual(footer, expected_footer)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    self._output_module.WriteEventBody(event, event_data, None)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2012-06-27 18:17:01')

    if sys.platform.startswith('win'):
      # The dict comparison is very picky on Windows hence we
      # have to make sure the drive letter is in the same case.
      expected_os_location = os.path.abspath('\\{0:s}'.format(
          os.path.join('cases', 'image.dd')))
    else:
      expected_os_location = '{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd'))

    expected_json_dict = {
        'event_0': {
            '__container_type__': 'event',
            '__type__': 'AttributeContainer',
            'data_type': 'test:output',
            'display_name': 'OS: /var/log/syslog.1',
            'hostname': 'ubuntu',
            'inode': 12345678,
            'message': (
                'Reporter <CRON> PID: |8442| (pam_unix(cron:session): '
                'session closed for user root)'),
            'pathspec': {
                '__type__': 'PathSpec',
                'type_indicator': 'TSK',
                'location': '/var/log/syslog.1',
                'inode': 15,
                'parent': {
                    '__type__': 'PathSpec',
                    'type_indicator': 'OS',
                    'location': expected_os_location,
                }
            },
            'text': (
                'Reporter <CRON> PID: |8442| (pam_unix(cron:session): '
                'session\n closed for user root)'),
            'timestamp': expected_timestamp,
            'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
            'username': 'root',
        }
    }
    event_body = self._output_writer.ReadOutput()

    # We need to compare dicts since we cannot determine the order
    # of values in the string.
    json_string = '{{ {0:s} }}'.format(event_body)
    json_dict = json.loads(json_string)
    self.assertEqual(json_dict, expected_json_dict)


if __name__ == '__main__':
  unittest.main()
