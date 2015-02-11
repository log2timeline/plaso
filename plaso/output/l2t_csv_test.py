#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the L2tCsv output class."""

import StringIO
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import eventdata
from plaso.output import l2t_csv


class L2tTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:l2t_csv'

  def __init__(self):
    """Initialize event with data."""
    super(L2tTestEvent, self).__init__()
    self.timestamp = 1340821021000000
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


formatters_manager.FormattersManager.RegisterFormatter(L2tTestEventFormatter)


class L2tCsvTest(unittest.TestCase):
  """Contains tests to validate the L2tCSV outputter."""
  def setUp(self):
    self.output = StringIO.StringIO()
    self.formatter = l2t_csv.L2tCsvOutputFormatter(None, self.output)
    self.event_object = L2tTestEvent()

  def testStart(self):
    """Test ensures header line is outputted as expected."""

    correct_line = (
        u'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        u'version,filename,inode,notes,format,extra\n')

    self.formatter.Start()
    self.assertEquals(self.output.getvalue(), correct_line)

  def testEventBody(self):
    """Test ensures that returned lines returned are formatted as L2tCSV."""

    self.formatter.EventBody(self.event_object)
    correct = (
        u'06/27/2012,18:17:01,UTC,M...,LOG,Syslog,Content Modification Time,-,'
        u'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root),Reporter <CRON> PID: 8442 '
        u'(pam_unix(cron:session): '
        u'session closed for user root),2,log/syslog.1,-,-,-,my_number: 123  '
        u'some_additional_foo: True \n')
    self.assertEquals(self.output.getvalue(), correct)

  def testEventBodyNoExtraCommas(self):
    """Test ensures that the only commas returned are the 16 delimeters."""

    self.formatter.EventBody(self.event_object)
    self.assertEquals(self.output.getvalue().count(u','), 16)


if __name__ == '__main__':
  unittest.main()
