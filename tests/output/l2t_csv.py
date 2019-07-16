#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the log2timeline (l2t) CSV output module."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import l2t_csv

from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class L2TTestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:l2t_csv'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class L2TCSVTest(test_lib.OutputModuleTestCase):
  """Tests for the L2tCSV output module."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:l2t_csv',
       'display_name': 'log/syslog.1',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'some_additional_foo': True,
       'a_binary_field': b'binary',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._formatter = l2t_csv.L2TCSVOutputModule(output_mediator)
    self._formatter.SetOutputWriter(self._output_writer)

  def testFormatField(self):
    """Tests the _FormatField function."""
    field_string = self._formatter._FormatField('test,ing')
    self.assertEqual(field_string, 'test ing')

  def testFormatHostname(self):
    """Tests the _FormatHostname function."""
    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    hostname_string = self._formatter._FormatHostname(event_data)
    self.assertEqual(hostname_string, 'ubuntu')

  def testFormatUsername(self):
    """Tests the _FormatUsername function."""
    _, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    username_string = self._formatter._FormatUsername(event_data)
    self.assertEqual(username_string, '-')

  def testGetOutputValues(self):
    """Tests the _GetOutputValues function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        L2TTestEventFormatter)

    expected_output_values = [
        '06/27/2012',
        '18:17:01',
        'UTC',
        '....',
        'LOG',
        'Syslog',
        '-',
        '-',
        'ubuntu',
        ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed '
         'for user root)'),
        ('Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed '
         'for user root)'),
        '2',
        'log/syslog.1',
        '-',
        '-',
        '-',
        'a_binary_field: binary; my_number: 123; some_additional_foo: True']

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    output_values = self._formatter._GetOutputValues(event, event_data, None)
    self.assertEqual(len(output_values), 17)
    self.assertEqual(output_values, expected_output_values)

    event.timestamp = -9223372036854775808
    output_values = self._formatter._GetOutputValues(event, event_data, None)
    self.assertEqual(len(output_values), 17)
    expected_output_values[0] = '00/00/0000'
    expected_output_values[1] = '--:--:--'
    self.assertEqual(output_values, expected_output_values)

    formatters_manager.FormattersManager.DeregisterFormatter(
        L2TTestEventFormatter)

  # TODO: add coverage for _WriteOutputValues

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    formatters_manager.FormattersManager.RegisterFormatter(
        L2TTestEventFormatter)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    self._formatter.WriteEventBody(event, event_data, event_tag)

    expected_event_body = (
        '06/27/2012,18:17:01,UTC,M...,LOG,Syslog,Content Modification Time,-,'
        'ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        'closed for user root),Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),'
        '2,log/syslog.1,-,Malware Printed,'
        '-,a_binary_field: binary; my_number: 123; some_additional_foo: True\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    # Ensure that the only commas returned are the 16 delimiters.
    self.assertEqual(event_body.count(','), 16)

    formatters_manager.FormattersManager.DeregisterFormatter(
        L2TTestEventFormatter)

  # TODO: add coverage for WriteEventMACBGroup

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = (
        'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        'version,filename,inode,notes,format,extra\n')

    self._formatter.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)


if __name__ == '__main__':
  unittest.main()
