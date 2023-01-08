#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the log2timeline (l2t) CSV output module."""

import io
import unittest

from dfvfs.path import fake_path_spec

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import l2t_csv

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class L2TCSVFieldFormattingHelperTest(test_lib.OutputModuleTestCase):
  """L2T CSV field formatting helper."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'_parser_chain': 'test_parser',
       'a_binary_field': b'binary',
       'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'path_spec': fake_path_spec.FakePathSpec(
           location='log/syslog.1'),
       'some_additional_foo': True,
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      {'_parser_chain': 'test_parser',
       'a_binary_field': b'binary',
       'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'path_spec': fake_path_spec.FakePathSpec(
           location='log/syslog.1'),
       'some_additional_foo': True,
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-28 00:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testFormatDate(self):
    """Tests the _FormatDate function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = l2t_csv.L2TCSVFieldFormattingHelper()

    # Test with event.date_time
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '06/27/2012')

    output_mediator.SetTimeZone('Australia/Sydney')

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '06/28/2012')

    output_mediator.SetTimeZone('UTC')

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    event.date_time._time_zone_offset = 600

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '06/27/2012')

    # Test with event.is_local_time
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    event.timestamp += 600 * 60 * 1000000
    event.date_time.is_local_time = True

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '06/28/2012')

    # Test with event.timestamp
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    event.date_time = None

    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '06/27/2012')

    event.timestamp = -9223372036854775808
    date_string = formatting_helper._FormatDate(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(date_string, '00/00/0000')

  def testFormatExtraAttributes(self):
    """Tests the _FormatExtraAttributes function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    formatting_helper = l2t_csv.L2TCSVFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    extra_attributes_string = formatting_helper._FormatExtraAttributes(
        output_mediator, event, event_data, event_data_stream)

    expected_extra_attributes_string = (
        'a_binary_field: binary; '
        'my_number: 123; '
        'some_additional_foo: True')
    self.assertEqual(extra_attributes_string, expected_extra_attributes_string)

  def testFormatParser(self):
    """Tests the _FormatParser function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = l2t_csv.L2TCSVFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    parser_string = formatting_helper._FormatParser(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(parser_string, 'test_parser')

  def testFormatType(self):
    """Tests the _FormatType function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = l2t_csv.L2TCSVFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    type_string = formatting_helper._FormatType(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(type_string, 'Content Modification Time')

  def testFormatVersion(self):
    """Tests the _FormatVersion function."""
    output_mediator = self._CreateOutputMediator()
    formatting_helper = l2t_csv.L2TCSVFieldFormattingHelper()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    version_string = formatting_helper._FormatVersion(
        output_mediator, event, event_data, event_data_stream)
    self.assertEqual(version_string, '2')


class L2TCSVTest(test_lib.OutputModuleTestCase):
  """Tests for the L2tCSV output module."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'_parser_chain': 'test_parser',
       'a_binary_field': b'binary',
       'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'path_spec': fake_path_spec.FakePathSpec(
           location='log/syslog.1'),
       'some_additional_foo': True,
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testGetFieldValues(self):
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = l2t_csv.L2TCSVOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    expected_field_values = {
        'date': '06/27/2012',
        'desc': ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
                 'closed for user root)'),
        'extra': ('a_binary_field: binary; my_number: 123; '
                  'some_additional_foo: True'),
        'filename': 'FAKE:log/syslog.1',
        'format': 'test_parser',
        'host': 'ubuntu',
        'inode': '-',
        'MACB': 'M...',
        'notes': 'Malware Printed',
        'short': ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
                  'session closed for user root)'),
        'source': 'FILE',
        'sourcetype': 'Test log file',
        'time': '18:17:01',
        'timezone': 'UTC',
        'type': 'Content Modification Time',
        'user': '-',
        'version': '2'}

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

    output_module = l2t_csv.L2TCSVOutputModule()
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
        '06/27/2012,18:17:01,UTC,M...,FILE,Test log file,Content Modification '
        'Time,-,ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
        'session closed for user root),Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),'
        '2,FAKE:log/syslog.1,-,Malware Printed,test_parser,a_binary_field: '
        'binary; my_number: 123; some_additional_foo: True\n')

    event_body = test_file_object.getvalue()
    self.assertEqual(event_body, expected_event_body)

    # Ensure that the only commas returned are the 16 delimiters.
    self.assertEqual(event_body.count(','), 16)

  # TODO: add coverage for WriteEventMACBGroup

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()

    output_module = l2t_csv.L2TCSVOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    expected_header = (
        'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        'version,filename,inode,notes,format,extra\n')

    header = test_file_object.getvalue()
    self.assertEqual(header, expected_header)


if __name__ == '__main__':
  unittest.main()
