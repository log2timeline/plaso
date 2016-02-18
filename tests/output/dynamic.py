#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dynamic output module."""

import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import dynamic

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class TestEvent(event.EventObject):
  DATA_TYPE = 'test:dynamic'

  def __init__(self):
    super(TestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.timestamp_desc = eventdata.EventTimestamp.CHANGE_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')


class TestEventFormatter(formatters_interface.EventFormatter):
  DATA_TYPE = 'test:dynamic'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Syslog'


class DynamicOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the dynamic output module."""

  # TODO: add coverage for _FormatTag.

  def testHeader(self):
    """Tests the WriteHeader function."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetOutputWriter(output_writer)
    expected_header = (
        b'datetime,timestamp_desc,source,source_long,message,parser,'
        b'display_name,tag\n')

    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        u'date', u'time', u'message', u'hostname', u'filename', u'some_stuff'])
    output_module.SetOutputWriter(output_writer)

    expected_header = b'date,time,message,hostname,filename,some_stuff\n'
    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        u'date', u'time', u'message', u'hostname', u'filename', u'some_stuff'])
    output_module.SetFieldDelimiter(u'@')
    output_module.SetOutputWriter(output_writer)

    expected_header = b'date@time@message@hostname@filename@some_stuff\n'
    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    event_object = TestEvent()

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        u'date', u'time', u'timezone', u'macb', u'source', u'sourcetype',
        u'type', u'user', u'host', u'message_short', u'message',
        u'filename', u'inode', u'notes', u'format', u'extra'])
    output_module.SetOutputWriter(output_writer)

    output_module.WriteHeader()
    expected_header = (
        b'date,time,timezone,macb,source,sourcetype,type,user,host,'
        b'message_short,message,filename,inode,notes,format,extra\n')
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    output_module.WriteEventBody(event_object)
    expected_event_body = (
        b'2012-06-27,18:17:01,UTC,..C.,LOG,Syslog,Metadata Modification Time,-,'
        b'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        b'closed for user root),Reporter <CRON> PID: 8442 '
        b'(pam_unix(cron:session): session closed for user root),log/syslog.1'
        b',-,-,-,-\n')
    event_body = output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    output_module.SetFields([
        u'datetime', u'nonsense', u'hostname', u'message'])
    output_module.SetOutputWriter(output_writer)

    expected_header = b'datetime,nonsense,hostname,message\n'
    output_module.WriteHeader()
    header = output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

    expected_event_body = (
        b'2012-06-27T18:17:01+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        b' (pam_unix(cron:session): session closed for user root)\n')

    output_module.WriteEventBody(event_object)
    event_body = output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)


if __name__ == '__main__':
  unittest.main()
