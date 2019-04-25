#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON output module."""

from __future__ import unicode_literals

import json
import os
import sys
import unittest

from plaso.lib import timelib
from plaso.output import json_out

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class JSONOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the JSON output module."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = json_out.JSONOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)
    self._event_object = test_lib.TestEventObject()

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
    self._output_module.WriteEventBody(self._event_object)

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
