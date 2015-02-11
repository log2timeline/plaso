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


class DynamicTest(unittest.TestCase):
  """Test the dynamic output module."""

  def testHeader(self):
    output = StringIO.StringIO()
    formatter = dynamic.DynamicOutput(None, output)
    correct_line = (
        'datetime,timestamp_desc,source,source_long,message,parser,'
        'display_name,tag,store_number,store_index\n')

    formatter.Start()
    self.assertEquals(output.getvalue(), correct_line)

    output = StringIO.StringIO()
    formatter = dynamic.DynamicOutput(None, output, filter_use=FakeFilter(
        ['date', 'time', 'message', 'hostname', 'filename', 'some_stuff']))

    correct_line = 'date,time,message,hostname,filename,some_stuff\n'
    formatter.Start()
    self.assertEquals(output.getvalue(), correct_line)

    output = StringIO.StringIO()
    formatter = dynamic.DynamicOutput(None, output, filter_use=FakeFilter(
        ['date', 'time', 'message', 'hostname', 'filename', 'some_stuff'],
        '@'))

    correct_line = 'date@time@message@hostname@filename@some_stuff\n'
    formatter.Start()
    self.assertEquals(output.getvalue(), correct_line)

  def testEventBody(self):
    """Test ensures that returned lines returned are fmt CSV as expected."""
    event_object = TestEvent()
    output = StringIO.StringIO()

    formatter = dynamic.DynamicOutput(None, output, filter_use=FakeFilter(
        ['date', 'time', 'timezone', 'macb', 'source', 'sourcetype', 'type',
         'user', 'host', 'message_short', 'message', 'filename',
         'inode', 'notes', 'format', 'extra']))

    formatter.Start()
    header = (
        'date,time,timezone,macb,source,sourcetype,type,user,host,'
        'message_short,message,filename,inode,notes,format,extra\n')
    self.assertEquals(output.getvalue(), header)

    formatter.EventBody(event_object)
    correct = (
        '2012-06-27,18:17:01,UTC,..C.,LOG,Syslog,Metadata Modification Time,-,'
        'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        'closed for user root),Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),log/syslog.1'
        ',-,-,-,-\n')
    self.assertEquals(output.getvalue(), header + correct)

    output = StringIO.StringIO()
    formatter = dynamic.DynamicOutput(None, output, filter_use=FakeFilter(
        ['datetime', 'nonsense', 'hostname', 'message']))

    header = 'datetime,nonsense,hostname,message\n'
    formatter.Start()
    self.assertEquals(output.getvalue(), header)

    correct = (
        '2012-06-27T18:17:01+00:00,-,ubuntu,Reporter <CRON> PID: 8442'
        ' (pam_unix(cron:session): session closed for user root)\n')

    formatter.EventBody(event_object)
    self.assertEquals(output.getvalue(), header + correct)


if __name__ == '__main__':
  unittest.main()
