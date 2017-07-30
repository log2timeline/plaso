#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline (l2t) CSV output module."""

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import l2t_csv

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class L2TTestEvent(events.EventObject):
  """Test event object."""
  DATA_TYPE = u'test:l2t_csv'

  def __init__(self):
    """Initializes an event object."""
    super(L2TTestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_WRITTEN
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root)')


class L2TTestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = u'test:l2t_csv'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class L2TCSVTest(test_lib.OutputModuleTestCase):
  """Tests for the L2tCSV output module."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._formatter = l2t_csv.L2TCSVOutputModule(output_mediator)
    self._formatter.SetOutputWriter(self._output_writer)

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = (
        b'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        b'version,filename,inode,notes,format,extra\n')

    self._formatter.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        L2TTestEventFormatter)

    event_tag = events.EventTag()
    event_tag.AddLabels([u'Malware', u'Printed'])

    event = L2TTestEvent()
    event.tag = event_tag

    self._formatter.WriteEventBody(event)

    expected_event_body = (
        b'06/27/2012,18:17:01,UTC,M...,LOG,Syslog,Content Modification Time,-,'
        b'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        b'closed for user root),Reporter <CRON> PID: 8442 '
        b'(pam_unix(cron:session): session closed for user root),'
        b'2,log/syslog.1,-,Malware Printed,'
        b'-,my_number: 123; some_additional_foo: True\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    # Ensure that the only commas returned are the 16 delimiters.
    self.assertEqual(event_body.count(b','), 16)

    formatters_manager.FormattersManager.DeregisterFormatter(
        L2TTestEventFormatter)


if __name__ == '__main__':
  unittest.main()
