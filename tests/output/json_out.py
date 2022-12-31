#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON output module."""

import json
import io
import os
import sys
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import definitions
from plaso.output import json_out

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class JSONOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the JSON output module."""

  # pylint: disable=protected-access

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'hostname': 'ubuntu',
       'path_spec': path_spec_factory.Factory.NewPathSpec(
           dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
           location='/var/log/syslog.1', parent=_OS_PATH_SPEC),
       'text': (
           'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'root'}]

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = json_out.JSONOutputModule()
    output_module._file_object = test_file_object

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # TODO: add test for event_tag.
    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    output_module._WriteFieldValues(output_mediator, field_values)

    expected_timestamp = shared_test_lib.CopyTimestampFromString(
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
            'date_time': {
                '__class_name__': 'PosixTimeInMicroseconds',
                '__type__': 'DateTimeValues',
                'timestamp': 1340821021000000,
            },
            'data_type': 'test:event',
            'display_name': 'TSK:/var/log/syslog.1',
            'filename': '/var/log/syslog.1',
            'hostname': 'ubuntu',
            'inode': '15',
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
    event_body = test_file_object.getvalue()

    # We need to compare dicts since we cannot determine the order
    # of values in the string.
    json_string = '{{ {0:s} }}'.format(event_body)
    json_dict = json.loads(json_string)
    self.assertEqual(json_dict, expected_json_dict)

  def testWriteFooter(self):
    """Tests the WriteFooter function."""
    test_file_object = io.StringIO()

    output_module = json_out.JSONOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteFooter()

    footer = test_file_object.getvalue()
    self.assertEqual(footer, '}')

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = json_out.JSONOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, '{')


if __name__ == '__main__':
  unittest.main()
