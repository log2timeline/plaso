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
from tests.output import test_lib


class TestEvent(events.EventObject):
  """Test event object."""
  DATA_TYPE = 'test:dynamic'

  def __init__(self):
    """Initializes an event object."""
    super(TestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_CHANGE
    self.hostname = 'ubuntu'
    self.filename = 'log/syslog.1'
    self.text = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        'closed for user root)')


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:dynamic'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class DynamicFieldsHelperTest(test_lib.OutputModuleTestCase):
  """Test the dynamic fields helper."""

  # pylint: disable=protected-access

  def testFormatDate(self):
    """Tests the _FormatDate function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    date_string = dynamic_fields_helper._FormatDate(event)
    self.assertEqual(date_string, '2012-06-27')

    event.timestamp = -9223372036854775808
    date_string = dynamic_fields_helper._FormatDate(event)
    self.assertEqual(date_string, '0000-00-00')

  def testFormatDateTime(self):
    """Tests the _FormatDateTime function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    date_time_string = dynamic_fields_helper._FormatDateTime(event)
    self.assertEqual(date_time_string, '2012-06-27T18:17:01+00:00')

    event.timestamp = -9223372036854775808
    date_time_string = dynamic_fields_helper._FormatDateTime(event)
    self.assertEqual(date_time_string, '0000-00-00T00:00:00')

  def testFormatHostname(self):
    """Tests the _FormatHostname function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    hostname_string = dynamic_fields_helper._FormatHostname(event)
    self.assertEqual(hostname_string, 'ubuntu')

  def testFormatInode(self):
    """Tests the _FormatInode function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    inode_string = dynamic_fields_helper._FormatInode(event)
    self.assertEqual(inode_string, '-')

  def testFormatMACB(self):
    """Tests the _FormatMACB function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    macb_string = dynamic_fields_helper._FormatMACB(event)
    self.assertEqual(macb_string, '..C.')

  def testFormatMessage(self):
    """Tests the _FormatMessage function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    message_string = dynamic_fields_helper._FormatMessage(event)
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

    event = TestEvent()
    message_short_string = dynamic_fields_helper._FormatMessageShort(event)
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

    event = TestEvent()
    source_string = dynamic_fields_helper._FormatSource(event)
    self.assertEqual(source_string, 'Syslog')

  def testFormatSourceShort(self):
    """Tests the _FormatSourceShort function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    source_short_string = dynamic_fields_helper._FormatSourceShort(event)
    self.assertEqual(source_short_string, 'LOG')

  def testFormatTag(self):
    """Tests the _FormatTag function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    tag_string = dynamic_fields_helper._FormatTag(event)
    self.assertEqual(tag_string, '-')

  def testFormatTime(self):
    """Tests the _FormatTime function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    time_string = dynamic_fields_helper._FormatTime(event)
    self.assertEqual(time_string, '18:17:01')

    event.timestamp = -9223372036854775808
    time_string = dynamic_fields_helper._FormatTime(event)
    self.assertEqual(time_string, '--:--:--')

  def testFormatTimestampDescription(self):
    """Tests the _FormatTimestampDescription function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    timestamp_description_string = (
        dynamic_fields_helper._FormatTimestampDescription(event))
    self.assertEqual(timestamp_description_string, 'Metadata Modification Time')

  def testFormatUsername(self):
    """Tests the _FormatUsername function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    username_string = dynamic_fields_helper._FormatUsername(event)
    self.assertEqual(username_string, '-')

  def testFormatZone(self):
    """Tests the _FormatZone function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    zone_string = dynamic_fields_helper._FormatZone(event)
    self.assertEqual(zone_string, 'UTC')

  # TODO: add coverage for _ReportEventError

  def testGetFormattedField(self):
    """Tests the GetFormattedField function."""
    output_mediator = self._CreateOutputMediator()
    dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)

    event = TestEvent()
    zone_string = dynamic_fields_helper.GetFormattedField(event, 'zone')
    self.assertEqual(zone_string, 'UTC')


class DynamicOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the dynamic output module."""

  # pylint: disable=protected-access

  # TODO: add coverage for _SanitizeField
  # TODO: add coverage for SetFieldDelimiter
  # TODO: add coverage for SetFields

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    event = TestEvent()

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

    output_module.WriteEventBody(event)
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

    output_module.WriteEventBody(event)
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
