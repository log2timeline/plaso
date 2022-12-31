#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the dynamic output module."""

import io
import os
import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import dynamic

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class DynamicFieldFormattingHelperTest(test_lib.OutputModuleTestCase):
  """Test the dynamic field formatting helper."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION},
      {'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-28 00:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION}]

  def testFormatDate(self):
    """Tests the _FormatDate function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = dynamic.DynamicFieldFormattingHelper()

    # Test with event.date_time
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-27')

    output_mediator.SetTimeZone('Australia/Sydney')

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-28')

    output_mediator.SetTimeZone('UTC')

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1]))
    event.date_time._time_zone_offset = 600

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-27')

    # Test with event.is_local_time
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    event.timestamp += 600 * 60 * 1000000
    event.date_time.is_local_time = True

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-28')

    # Test with event.timestamp
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    event.date_time = None

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-27')

    event.timestamp = 0
    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '0000-00-00')

    event.timestamp = -9223372036854775808
    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '0000-00-00')

  def testFormatTimestampDescription(self):
    """Tests the _FormatTimestampDescription function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = dynamic.DynamicFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    timestamp_description_string = (
        formatting_helper._FormatTimestampDescription(
            output_mediator, event, event_data, event_data_stream))
    self.assertEqual(timestamp_description_string, 'Metadata Modification Time')


class DynamicOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the dynamic output module."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION}]

  def testGetFieldValues(self):
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = dynamic.DynamicOutputModule()

    output_module.SetFields([
        'date', 'time', 'timezone', 'macb', 'source', 'sourcetype',
        'type', 'user', 'host', 'message_short', 'message',
        'filename', 'inode', 'notes', 'format', 'extra'])

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    expected_field_values = {
        'date': '2012-06-27',
        'extra': '-',
        'filename': 'log/syslog.1',
        'format': '-',
        'host': 'ubuntu',
        'inode': '-',
        'macb': '..C.',
        'message': (
            'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
            'closed for user root)'),
        'message_short': (
            'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
            'closed for user root)'),
        'notes': '-',
        'source': 'FILE',
        'sourcetype': 'Test log file',
        'time': '18:17:01',
        'timezone': 'UTC',
        'type': 'Metadata Modification Time',
        'user': '-'}

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self.assertEqual(field_values, expected_field_values)

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = dynamic.DynamicOutputModule()
    output_module._file_object = test_file_object

    output_module.SetFields([
        'date', 'time', 'timezone', 'macb', 'source', 'sourcetype',
        'type', 'user', 'host', 'message_short', 'message',
        'filename', 'inode', 'notes', 'format', 'extra'])

    output_module.WriteHeader(output_mediator)

    expected_header = (
        'date,time,timezone,macb,source,sourcetype,type,user,host,'
        'message_short,message,filename,inode,notes,format,extra\n')

    header = test_file_object.getvalue()
    self.assertEqual(header, expected_header)

    test_file_object.seek(0, os.SEEK_SET)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    output_module._WriteFieldValues(output_mediator, field_values)

    output_module._FlushSortedStringsHeap()

    expected_event_body = (
        '2012-06-27,18:17:01,UTC,..C.,FILE,Test log file,Metadata '
        'Modification Time,-,ubuntu,Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),Reporter '
        '<CRON> PID: 8442 (pam_unix(cron:session): session closed for user '
        'root),log/syslog.1,-,-,-,-\n')

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, expected_event_body)

    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = dynamic.DynamicOutputModule()
    output_module._file_object = test_file_object

    output_module.SetFields(['datetime', 'nonsense', 'hostname', 'message'])

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, 'datetime,nonsense,hostname,message\n')

    test_file_object.seek(0, os.SEEK_SET)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    output_module._WriteFieldValues(output_mediator, field_values)

    output_module._FlushSortedStringsHeap()

    expected_event_body = (
        '2012-06-27T18:17:01.000000+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)\n')

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, expected_event_body)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    expected_header = (
        'datetime,timestamp_desc,source,source_long,message,parser,'
        'display_name,tag\n')

    header = test_file_object.getvalue()
    self.assertEqual(header, expected_header)

    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule()
    output_module._file_object = test_file_object

    output_module.SetFields([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, 'date,time,message,hostname,filename,some_stuff\n')

    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule()
    output_module._file_object = test_file_object

    output_module.SetFields([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])
    output_module.SetFieldDelimiter('@')

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, 'date@time@message@hostname@filename@some_stuff\n')


if __name__ == '__main__':
  unittest.main()
