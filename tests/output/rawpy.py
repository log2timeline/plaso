#!/usr/bin/env python3
"""Tests for the native (or "raw") Python output module."""


import io
import os
import sys
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import definitions
from plaso.output import rawpy

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class NativePythonOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the "raw" (or native) Python output module."""

  # pylint: disable=protected-access

  _OS_LOCATION = os.path.join(os.path.sep, 'cases', 'image.dd')

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location=_OS_LOCATION)

  _TEST_EVENTS = [
      {'data_type': 'test:output',
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

  def testGetFieldValues(self):
    """Tests the GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = rawpy.NativePythonOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()

    expected_field_values = {
        '_event_identifier': event_identifier_string,
        '_timestamp': '2012-06-27T18:17:01.000000+00:00',
        'data_type': 'test:output',
        'display_name': 'TSK:/var/log/syslog.1',
        'filename': '/var/log/syslog.1',
        'hostname': 'ubuntu',
        'inode': '15',
        'path_spec': event_data_stream.path_spec,
        'text': ('Reporter <CRON> PID: |8442| (pam_unix(cron:session): '
                 'session\n closed for user root)'),
        'username': 'root'}

    # TODO: add test for event_tag.
    field_values = output_module.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    self.assertEqual(field_values, expected_field_values)

  def testWriteFieldValues(self):
    """Tests the WriteFieldValues function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = rawpy.NativePythonOutputModule()
    output_module._file_object = test_file_object

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # TODO: add test for event_tag.
    field_values = output_module.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    output_module.WriteFieldValues(output_mediator, field_values)

    expected_os_location = os.path.join(os.path.sep, 'cases', 'image.dd')
    if sys.platform.startswith('win'):
      # The dict comparison is very picky on Windows hence we have to make
      # sure the drive letter is in the same case.
      expected_os_location = os.path.abspath(expected_os_location)

    expected_event_body = (
        f'+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-\n'
        f'[Timestamp]:\n'
        f'  2012-06-27T18:17:01.000000+00:00\n'
        f'\n'
        f'[Pathspec]:\n'
        f'  type: OS, location: {expected_os_location!s}\n'
        f'  type: TSK, inode: 15, location: /var/log/syslog.1\n'
        f'\n'
        f'[Reserved attributes]:\n'
        f'  {{data_type}} test:output\n'
        f'  {{display_name}} TSK:/var/log/syslog.1\n'
        f'  {{filename}} /var/log/syslog.1\n'
        f'  {{hostname}} ubuntu\n'
        f'  {{inode}} 15\n'
        f'  {{username}} root\n'
        f'\n'
        f'[Additional attributes]:\n'
        f'  {{text}} Reporter <CRON> PID: |8442| (pam_unix(cron:session): '
        f'session\n'
        f' closed for user root)\n'
        f'\n')

    event_body = test_file_object.getvalue()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(event_body.split('\n'), expected_event_body.split('\n'))


if __name__ == '__main__':
  unittest.main()
