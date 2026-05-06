#!/usr/bin/env python3
"""Tests for the KML output module."""

import io
import os
import sys
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import definitions
from plaso.output import kml

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class KMLOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the KML output module."""

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
       'username': 'root'},
      {'data_type': 'test:output',
       'hostname': 'ubuntu',
       'latitude': 37.4222899014,
       'longitude': -122.082203543,
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
    """Tests the WriteFieldValues function."""
    # Test event without geo-location.
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = kml.KMLOutputModule()
    output_module._file_object = test_file_object

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # TODO: add test for event_tag.
    field_values = output_module.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    output_module.WriteFieldValues(output_mediator, field_values)

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, '')

    # Test event with geo-location.
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = kml.KMLOutputModule()
    output_module._file_object = test_file_object

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1]))

    # TODO: add test for event_tag.
    field_values = output_module.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, None)

    output_module.WriteFieldValues(output_mediator, field_values)

    event_body = test_file_object.getvalue()

    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()

    expected_os_location = os.path.join(os.path.sep, 'cases', 'image.dd')
    if sys.platform.startswith('win'):
      # The dict comparison is very picky on Windows hence we have to make
      # sure the drive letter is in the same case.
      expected_os_location = os.path.abspath(expected_os_location)

    expected_event_body_lines = [
        (f'<Placemark><name>{event_identifier_string!s}</name><description>'
         f'+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-'
         f'+-+-+-+-+-+-'),
        '[Timestamp]:',
        '  2012-06-27T18:17:01.000000+00:00',
        '',
        '[Pathspec]:',
        f'  type: OS, location: {expected_os_location!s}',
        '  type: TSK, inode: 15, location: /var/log/syslog.1',
        '',
        '[Reserved attributes]:',
        '  {data_type} test:output',
        '  {display_name} TSK:/var/log/syslog.1',
        '  {filename} /var/log/syslog.1',
        '  {hostname} ubuntu',
        '  {inode} 15',
        '  {username} root',
        '',
        '[Additional attributes]:',
        '  {latitude} 37.4222899014',
        '  {longitude} -122.082203543',
        ('  {text} Reporter &lt;CRON&gt; PID: |8442| (pam_unix(cron:session): '
         'session'),
        ' closed for user root)',
        '',
        ('</description>'
         '<Point><coordinates>-122.082203543,37.4222899014</coordinates>'
         '</Point></Placemark>')]

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(event_body.split('\n'), expected_event_body_lines)

  def testWriteFooter(self):
    """Tests the WriteFooter function."""
    test_file_object = io.StringIO()

    output_module = kml.KMLOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteFooter()

    footer = test_file_object.getvalue()
    self.assertEqual(footer, '</Document></kml>')

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = kml.KMLOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    expected_header = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>')

    header = test_file_object.getvalue()
    self.assertEqual(header, expected_header)


if __name__ == '__main__':
  unittest.main()
