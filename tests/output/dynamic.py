#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the dynamic output module."""

import io
import os
import unittest

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
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}]

  def testFormatDate(self):
    """Tests the _FormatDate function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = dynamic.DynamicFieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    # Test with event.date_time
    date_string = formatting_helper._FormatDate(
        event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-27')

    output_mediator.SetTimezone('Australia/Sydney')

    date_string = formatting_helper._FormatDate(
        event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-28')

    output_mediator.SetTimezone('UTC')

    # Test with event.timestamp
    event.date_time = None
    date_string = formatting_helper._FormatDate(
        event, event_data, event_data_stream)
    self.assertEqual(date_string, '2012-06-27')

    event.timestamp = 0
    date_string = formatting_helper._FormatDate(
        event, event_data, event_data_stream)
    self.assertEqual(date_string, '0000-00-00')

    event.timestamp = -9223372036854775808
    date_string = formatting_helper._FormatDate(
        event, event_data, event_data_stream)
    self.assertEqual(date_string, '0000-00-00')

  def testFormatTimestampDescription(self):
    """Tests the _FormatTimestampDescription function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = dynamic.DynamicFieldFormattingHelper(output_mediator)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    timestamp_description_string = (
        formatting_helper._FormatTimestampDescription(
            event, event_data, event_data_stream))
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
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}]

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module._file_object = test_file_object

    output_module.SetFields([
        'date', 'time', 'timezone', 'macb', 'source', 'sourcetype',
        'type', 'user', 'host', 'message_short', 'message',
        'filename', 'inode', 'notes', 'format', 'extra'])

    output_module.WriteHeader()

    expected_header = (
        'date,time,timezone,macb,source,sourcetype,type,user,host,'
        'message_short,message,filename,inode,notes,format,extra\n')

    header = test_file_object.getvalue()
    self.assertEqual(header, expected_header)

    test_file_object.seek(0, os.SEEK_SET)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    output_module.WriteEventBody(event, event_data, event_data_stream, None)

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

    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module._file_object = test_file_object

    output_module.SetFields(['datetime', 'nonsense', 'hostname', 'message'])

    output_module.WriteHeader()

    header = test_file_object.getvalue()
    self.assertEqual(header, 'datetime,nonsense,hostname,message\n')

    test_file_object.seek(0, os.SEEK_SET)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    output_module.WriteEventBody(event, event_data, event_data_stream, None)

    expected_event_body = (
        '2012-06-27T18:17:01.000000+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)\n')

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, expected_event_body)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module._file_object = test_file_object

    output_module.WriteHeader()

    expected_header = (
        'datetime,timestamp_desc,source,source_long,message,parser,'
        'display_name,tag\n')

    header = test_file_object.getvalue()
    self.assertEqual(header, expected_header)

    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module._file_object = test_file_object

    output_module.SetFields([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])

    output_module.WriteHeader()

    header = test_file_object.getvalue()
    self.assertEqual(header, 'date,time,message,hostname,filename,some_stuff\n')

    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module._file_object = test_file_object

    output_module.SetFields([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])
    output_module.SetFieldDelimiter('@')

    output_module.WriteHeader()

    header = test_file_object.getvalue()
    self.assertEqual(header, 'date@time@message@hostname@filename@some_stuff\n')


if __name__ == '__main__':
  unittest.main()
