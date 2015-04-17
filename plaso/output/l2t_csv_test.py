#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline (l2t) CSV output class."""

import unittest

from plaso.cli import test_lib as cli_test_lib
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import l2t_csv
from plaso.output import test_lib


class L2tTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:l2t_csv'

  def __init__(self):
    """Initialize event with data."""
    super(L2tTestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')


class L2tTestEventFormatter(formatters_interface.EventFormatter):
  """Formatter for the test event."""
  DATA_TYPE = 'test:l2t_csv'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class L2TCSVTest(test_lib.OutputModuleTestCase):
  """Contains tests to validate the L2tCSV outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self.formatter = l2t_csv.L2TCSVOutputModule(
        output_mediator, output_writer=self._output_writer)
    self.event_object = L2tTestEvent()

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = (
        b'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        b'version,filename,inode,notes,format,extra\n')

    self.formatter.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        L2tTestEventFormatter)

    event_tag = event.EventTag()
    event_tag.tags = [u'Malware', u'Document Printed']
    event_tag.uuid = self.event_object.uuid

    self.event_object.tag = event_tag
    self.formatter.WriteEventBody(self.event_object)

    expected_event_body = (
        b'06/27/2012,18:17:01,UTC,M...,LOG,Syslog,Content Modification Time,-,'
        b'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        b'closed for user root),Reporter <CRON> PID: 8442 '
        b'(pam_unix(cron:session): session closed for user root),'
        b'2,log/syslog.1,-,Malware Document Printed,'
        b'-,my_number: 123  some_additional_foo: True \n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    # Ensure that the only commas returned are the 16 delimeters.
    self.assertEqual(event_body.count(b','), 16)

    formatters_manager.FormattersManager.DeregisterFormatter(
        L2tTestEventFormatter)


if __name__ == '__main__':
  unittest.main()
