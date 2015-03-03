#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dynamic output formatter for plaso."""

import StringIO
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import eventdata
from plaso.output import dynamic
from plaso.output import test_lib


class TestEvent(event.EventObject):
  DATA_TYPE = 'test:dynamic'

  def __init__(self):
    super(TestEvent, self).__init__()
    self.timestamp = 1340821021000000
    self.timestamp_desc = eventdata.EventTimestamp.CHANGE_TIME
    self.hostname = 'ubuntu'
    self.filename = 'log/syslog.1'
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')


class TestEventFormatter(formatters_interface.EventFormatter):
  DATA_TYPE = 'test:dynamic'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


formatters_manager.FormattersManager.RegisterFormatter(TestEventFormatter)


class FakeFilter(object):
  """Provide a fake filter, that defines which fields to use."""

  def __init__(self, fields, separator=u','):
    self.fields = fields
    self.separator = separator


class DynamicOutputTest(test_lib.LogOutputFormatterTestCase):
  """Test the dynamic output module."""

  def testHeader(self):
    output = StringIO.StringIO()
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output)
    correct_line = (
        'datetime,timestamp_desc,source,source_long,message,parser,'
        'display_name,tag,store_number,store_index\n')

    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), correct_line)

    output = StringIO.StringIO()
    filter_object = FakeFilter([
        'date', 'time', 'message', 'hostname', 'filename', 'some_stuff'])
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    correct_line = 'date,time,message,hostname,filename,some_stuff\n'
    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), correct_line)

    output = StringIO.StringIO()
    filter_object = FakeFilter(
        ['date', 'time', 'message', 'hostname', 'filename', 'some_stuff'],
        separator='@')
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    correct_line = 'date@time@message@hostname@filename@some_stuff\n'
    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), correct_line)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    event_object = TestEvent()
    output = StringIO.StringIO()

    filter_object = FakeFilter([
        'date', 'time', 'timezone', 'macb', 'source', 'sourcetype', 'type',
        'user', 'host', 'message_short', 'message', 'filename',
        'inode', 'notes', 'format', 'extra'])
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    formatter.WriteHeader()
    header = (
        'date,time,timezone,macb,source,sourcetype,type,user,host,'
        'message_short,message,filename,inode,notes,format,extra\n')
    self.assertEqual(output.getvalue(), header)

    formatter.WriteEventBody(event_object)
    correct = (
        '2012-06-27,18:17:01,UTC,..C.,LOG,Syslog,Metadata Modification Time,-,'
        'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        'closed for user root),Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),log/syslog.1'
        ',-,-,-,-\n')
    self.assertEqual(output.getvalue(), header + correct)

    output = StringIO.StringIO()
    filter_object = FakeFilter(['datetime', 'nonsense', 'hostname', 'message'])
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    header = 'datetime,nonsense,hostname,message\n'
    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), header)

    correct = (
        '2012-06-27T18:17:01+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)\n')

    formatter.WriteEventBody(event_object)
    self.assertEqual(output.getvalue(), header + correct)


if __name__ == '__main__':
  unittest.main()
