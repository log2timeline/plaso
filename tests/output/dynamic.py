#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the dynamic output module."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import dynamic

from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:dynamic'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class DynamicFieldsHelperTest(test_lib.OutputModuleTestCase):
  """Test the dynamic fields helper."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:dynamic',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}]

  def testFormatDate(self):
    """Tests the _FormatDate function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    date_string = dynamic_fields_helper._FormatDate(event, event_data)
    self.assertEqual(date_string, '2012-06-27')

    event.timestamp = -9223372036854775808
    date_string = dynamic_fields_helper._FormatDate(event, event_data)
    self.assertEqual(date_string, '0000-00-00')

  def testFormatDateTime(self):
    """Tests the _FormatDateTime function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    date_time_string = dynamic_fields_helper._FormatDateTime(event, event_data)
    self.assertEqual(date_time_string, '2012-06-27T18:17:01+00:00')

    event.timestamp = -9223372036854775808
    date_time_string = dynamic_fields_helper._FormatDateTime(event, event_data)
    self.assertEqual(date_time_string, '0000-00-00T00:00:00')

  def testFormatHostname(self):
    """Tests the _FormatHostname function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    hostname_string = dynamic_fields_helper._FormatHostname(event, event_data)
    self.assertEqual(hostname_string, 'ubuntu')

  def testFormatInode(self):
    """Tests the _FormatInode function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    inode_string = dynamic_fields_helper._FormatInode(event, event_data)
    self.assertEqual(inode_string, '-')

  def testFormatMACB(self):
    """Tests the _FormatMACB function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    macb_string = dynamic_fields_helper._FormatMACB(event, event_data)
    self.assertEqual(macb_string, '..C.')

  def testFormatMessage(self):
    """Tests the _FormatMessage function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    message_string = dynamic_fields_helper._FormatMessage(event, event_data)
    expected_message_string = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed '
        'for user root)')
    self.assertEqual(message_string, expected_message_string)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testFormatMessageShort(self):
    """Tests the _FormatMessageShort function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    message_short_string = dynamic_fields_helper._FormatMessageShort(
        event, event_data)
    expected_message_short_string = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed '
        'for user root)')
    self.assertEqual(message_short_string, expected_message_short_string)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testFormatSource(self):
    """Tests the _FormatSource function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    source_string = dynamic_fields_helper._FormatSource(event, event_data)
    self.assertEqual(source_string, 'Syslog')

  def testFormatSourceShort(self):
    """Tests the _FormatSourceShort function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    source_short_string = dynamic_fields_helper._FormatSourceShort(
        event, event_data)
    self.assertEqual(source_short_string, 'LOG')

  def testFormatTag(self):
    """Tests the _FormatTag function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    tag_string = dynamic_fields_helper._FormatTag(None)
    self.assertEqual(tag_string, '-')

    event_tag = events.EventTag()
    event_tag.AddLabel('one')
    event_tag.AddLabel('two')

    tag_string = dynamic_fields_helper._FormatTag(event_tag)
    self.assertEqual(tag_string, 'one two')

  def testFormatTime(self):
    """Tests the _FormatTime function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    time_string = dynamic_fields_helper._FormatTime(event, event_data)
    self.assertEqual(time_string, '18:17:01')

    event.timestamp = -9223372036854775808
    time_string = dynamic_fields_helper._FormatTime(event, event_data)
    self.assertEqual(time_string, '--:--:--')

  def testFormatTimestampDescription(self):
    """Tests the _FormatTimestampDescription function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    timestamp_description_string = (
        dynamic_fields_helper._FormatTimestampDescription(event, event_data))
    self.assertEqual(timestamp_description_string, 'Metadata Modification Time')

  def testFormatUsername(self):
    """Tests the _FormatUsername function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    username_string = dynamic_fields_helper._FormatUsername(event, event_data)
    self.assertEqual(username_string, '-')

  def testFormatZone(self):
    """Tests the _FormatZone function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    zone_string = dynamic_fields_helper._FormatZone(event, event_data)
    self.assertEqual(zone_string, 'UTC')

  # TODO: add coverage for _ReportEventError

  def testGetFormattedField(self):
    """Tests the GetFormattedField function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    zone_string = dynamic_fields_helper.GetFormattedField(
        event, event_data, None, 'zone')
    self.assertEqual(zone_string, 'UTC')


class DynamicOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the dynamic output module."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:dynamic',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}]

  # TODO: add coverage for _SanitizeField
  # TODO: add coverage for SetFieldDelimiter
  # TODO: add coverage for SetFields

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        'date', 'time', 'timezone', 'macb', 'source', 'sourcetype',
        'type', 'user', 'host', 'message_short', 'message',
        'filename', 'inode', 'notes', 'format', 'extra'])
    output_module.SetOutputWriter(output_writer)

    output_module.WriteHeader()
    expected_header = (
        'date,time,timezone,macb,source,sourcetype,type,user,host,'
        'message_short,message,filename,inode,notes,format,extra\n')
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    output_module.WriteEventBody(event, event_data, None)
    expected_event_body = (
        '2012-06-27,18:17:01,UTC,..C.,LOG,Syslog,Metadata Modification Time,-,'
        'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        'closed for user root),Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),log/syslog.1'
        ',-,-,-,-\n')
    event_body = output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        'datetime', 'nonsense', 'hostname', 'message'])
    output_module.SetOutputWriter(output_writer)

    expected_header = 'datetime,nonsense,hostname,message\n'
    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    expected_event_body = (
        '2012-06-27T18:17:01+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)\n')

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    output_module.WriteEventBody(event, event_data, None)
    event_body = output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)

  def testHeader(self):
    """Tests the WriteHeader function."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    expected_header = (
        'datetime,timestamp_desc,source,source_long,message,parser,'
        'display_name,tag\n')

    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])
    output_module.SetOutputWriter(output_writer)

    expected_header = 'date,time,message,hostname,filename,some_stuff\n'
    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])
    output_module.SetFieldDelimiter('@')
    output_module.SetOutputWriter(output_writer)

    expected_header = 'date@time@message@hostname@filename@some_stuff\n'
    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)


if __name__ == '__main__':
  unittest.main()
