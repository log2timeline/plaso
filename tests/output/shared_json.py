#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared functionality for JSON output modules."""

from __future__ import unicode_literals

import os
import sys
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import shared_json

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class SharedJSONOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the shared functionality for JSON output modules."""

  # pylint: disable=protected-access

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

  def testWriteSerialized(self):
    """Tests the _WriteSerialized function."""
    output_mediator = self._CreateOutputMediator()
    output_module = shared_json.SharedJSONOutputModule(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    if sys.platform.startswith('win'):
      # The dict comparison is very picky on Windows hence we
      # have to make sure the drive letter is in the same case.
      expected_os_location = os.path.abspath('\\{0:s}'.format(
          os.path.join('cases', 'image.dd')))
      expected_os_location = expected_os_location.replace('\\', '\\\\')
    else:
      expected_os_location = '{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd'))

    expected_json_string = (
        '{{"__container_type__": "event", "__type__": "AttributeContainer", '
        '"data_type": "test:output", "display_name": "OS: /var/log/syslog.1", '
        '"hostname": "ubuntu", "inode": 12345678, "message": "Reporter <CRON> '
        'PID: |8442| (pam_unix(cron:session): session closed for user root)", '
        '"pathspec": {{"__type__": "PathSpec", "inode": 15, "location": '
        '"/var/log/syslog.1", "parent": {{"__type__": "PathSpec", "location": '
        '"{0:s}", "type_indicator": "OS"}}, "type_indicator": "TSK"}}, "text": '
        '"Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\\n '
        'closed for user root)", "timestamp": 1340821021000000, '
        '"timestamp_desc": "Unknown Time", "username": "root"}}').format(
            expected_os_location)

    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    json_string = output_module._WriteSerialized(event, event_data, None)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)

    self.assertEqual(json_string, expected_json_string)

  def testWriteSerializedDict(self):
    """Tests the _WriteSerializedDict function."""
    output_mediator = self._CreateOutputMediator()
    output_module = shared_json.SharedJSONOutputModule(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

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
        '__container_type__': 'event',
        '__type__': 'AttributeContainer',
        'data_type': 'test:output',
        'display_name': 'OS: /var/log/syslog.1',
        'hostname': 'ubuntu',
        'inode': 12345678,
        'message': (
            'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session '
            'closed for user root)'),
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
    formatters_manager.FormattersManager.RegisterFormatter(
        test_lib.TestEventFormatter)

    json_dict = output_module._WriteSerializedDict(
        event, event_data, None)

    formatters_manager.FormattersManager.DeregisterFormatter(
        test_lib.TestEventFormatter)

    self.assertEqual(json_dict, expected_json_dict)


if __name__ == '__main__':
  unittest.main()
