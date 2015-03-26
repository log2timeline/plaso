#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dynamic output formatter for plaso."""

import io
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import dynamic
from plaso.output import test_lib


class TestEvent(event.EventObject):
  DATA_TYPE = 'test:dynamic'

  def __init__(self):
    super(TestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
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


class FakeFilter(object):
  """Provide a fake filter, that defines which fields to use."""

  def __init__(self, fields, separator=u','):
    super(FakeFilter, self).__init__()
    self.fields = fields
    self.separator = separator


class DynamicOutputTest(test_lib.LogOutputFormatterTestCase):
  """Test the dynamic output module."""

  def testHeader(self):
    """Tests the WriteHeader function."""
    output = io.BytesIO()
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output)
    expected_header = (
        b'datetime,timestamp_desc,source,source_long,message,parser,'
        b'display_name,tag,store_number,store_index\n')

    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), expected_header)

    output = io.BytesIO()
    filter_object = FakeFilter([
        u'date', u'time', u'message', u'hostname', u'filename', u'some_stuff'])
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    expected_header = b'date,time,message,hostname,filename,some_stuff\n'
    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), expected_header)

    output = io.BytesIO()
    filter_object = FakeFilter(
        [u'date', u'time', u'message', u'hostname', u'filename', u'some_stuff'],
        separator='@')
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    expected_header = b'date@time@message@hostname@filename@some_stuff\n'
    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestEventFormatter)

    event_object = TestEvent()
    output = io.BytesIO()

    filter_object = FakeFilter([
        u'date', u'time', u'timezone', u'macb', u'source', u'sourcetype',
        u'type', u'user', u'host', u'message_short', u'message',
        u'filename', u'inode', u'notes', u'format', u'extra'])
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    formatter.WriteHeader()
    expected_header = (
        b'date,time,timezone,macb,source,sourcetype,type,user,host,'
        b'message_short,message,filename,inode,notes,format,extra\n')
    self.assertEqual(output.getvalue(), expected_header)

    formatter.WriteEventBody(event_object)
    expected_event_body = (
        b'{0:s}'
        b'2012-06-27,18:17:01,UTC,..C.,LOG,Syslog,Metadata Modification Time,-,'
        b'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        b'closed for user root),Reporter <CRON> PID: 8442 '
        b'(pam_unix(cron:session): session closed for user root),log/syslog.1'
        b',-,-,-,-\n').format(expected_header)
    self.assertEqual(output.getvalue(), expected_event_body)

    output = io.BytesIO()
    filter_object = FakeFilter([
        u'datetime', u'nonsense', u'hostname', u'message'])
    formatter = dynamic.DynamicOutput(
        None, self._formatter_mediator, filehandle=output,
        filter_use=filter_object)

    expected_header = b'datetime,nonsense,hostname,message\n'
    formatter.WriteHeader()
    self.assertEqual(output.getvalue(), expected_header)

    expected_event_body = (
        b'{0:s}'
        b'2012-06-27T18:17:01+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        b' (pam_unix(cron:session): session closed for user root)\n').format(
            expected_header)

    formatter.WriteEventBody(event_object)
    self.assertEqual(output.getvalue(), expected_event_body)

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestEventFormatter)


if __name__ == '__main__':
  unittest.main()
