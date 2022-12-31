#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the TLN output class."""

import io
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import tln

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TLNFieldFormattingHelperTest(test_lib.OutputModuleTestCase):
  """Test the TLN output module field formatting helper."""

  # pylint: disable=protected-access

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
       'path_spec': path_spec_factory.Factory.NewPathSpec(
           dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
           location='/var/log/syslog.1', parent=_OS_PATH_SPEC),
       'text': (
           'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'root'}]

  def testFormatDescription(self):
    """Tests the _FormatDescription function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    formatting_helper = tln.TLNFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    description_string = formatting_helper._FormatDescription(
        output_mediator, event, event_data, event_data_stream)

    expected_description_string = (
        '2012-06-27T18:17:01.000000+00:00; '
        'Unknown Time; '
        'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session closed '
        'for user root)')
    self.assertEqual(description_string, expected_description_string)

  def testFormatNotes(self):
    """Tests the _FormatNotes function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = tln.TLNFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    notes_string = formatting_helper._FormatNotes(
        output_mediator, event, event_data, event_data_stream)

    self.assertEqual(
        notes_string, 'File: OS: /var/log/syslog.1 inode: 12345678')

  def test_FormatTimestamp(self):
    """Tests the __FormatTimestamp function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = tln.TLNFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    timestamp_string = formatting_helper._FormatTimestamp(
        output_mediator, event, event_data, event_data_stream)

    self.assertEqual(timestamp_string, '1340821021')


class TLNOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the TLN output module."""

  # pylint: disable=protected-access

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
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
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = tln.TLNOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    expected_field_values = {
        'description': (
            '2012-06-27T18:17:01.000000+00:00; Unknown Time; Reporter <CRON> '
            'PID:  8442  (pam_unix(cron:session): session closed for user '
            'root)'),
        'host': 'ubuntu',
        'source': 'FILE',
        'time': '1340821021',
        'user': 'root'}

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self.assertEqual(field_values, expected_field_values)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = tln.TLNOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, 'Time|Source|Host|User|Description\n')

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = tln.TLNOutputModule()
    output_module._file_object = test_file_object

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    output_module._WriteFieldValues(output_mediator, field_values)

    output_module._FlushSortedStringsHeap()

    expected_event_body = (
        '1340821021|FILE|ubuntu|root|2012-06-27T18:17:01.000000+00:00; '
        'Unknown Time; '
        'Reporter <CRON> PID:  8442  (pam_unix(cron:session): '
        'session closed for user root)\n')

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, expected_event_body)
    self.assertEqual(event_body.count('|'), 4)


class L2TTLNOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the log2timeline TLN output module."""

  # pylint: disable=protected-access

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
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
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = tln.L2TTLNOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    expected_field_values = {
        'description': (
            '2012-06-27T18:17:01.000000+00:00; Unknown Time; Reporter <CRON> '
            'PID:  8442  (pam_unix(cron:session): session closed for user '
            'root)'),
        'host': 'ubuntu',
        'notes': 'File: OS: /var/log/syslog.1 inode: 12345678',
        'source': 'FILE',
        'time': '1340821021',
        'tz': 'UTC',
        'user': 'root'}

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self.assertEqual(field_values, expected_field_values)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = tln.L2TTLNOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, 'Time|Source|Host|User|Description|TZ|Notes\n')

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = tln.L2TTLNOutputModule()
    output_module._file_object = test_file_object
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    output_module._WriteFieldValues(output_mediator, field_values)

    output_module._FlushSortedStringsHeap()

    expected_event_body = (
        '1340821021|FILE|ubuntu|root|2012-06-27T18:17:01.000000+00:00; '
        'Unknown Time; '
        'Reporter <CRON> PID:  8442  (pam_unix(cron:session): '
        'session closed for user root)'
        '|UTC|File: OS: /var/log/syslog.1 inode: 12345678\n')

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, expected_event_body)

    self.assertEqual(event_body.count('|'), 6)


if __name__ == '__main__':
  unittest.main()
