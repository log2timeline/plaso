#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the log2timeline (l2t) CSV output module."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions
from plaso.output import l2t_csv

from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.formatters import test_lib as formatters_test_lib
from tests.output import test_lib


class L2TCSVTest(test_lib.OutputModuleTestCase):
  """Tests for the L2tCSV output module."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'display_name': 'log/syslog.1',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'parser': 'test_parser',
       'some_additional_foo': True,
       'a_binary_field': b'binary',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = l2t_csv.L2TCSVOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)

  def testFormatField(self):
    """Tests the _FormatField function."""
    field_string = self._output_module._FormatField('test,ing')
    self.assertEqual(field_string, 'test ing')

  def testFormatHostname(self):
    """Tests the _FormatHostname function."""
    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    hostname_string = self._output_module._FormatHostname(event_data)
    self.assertEqual(hostname_string, 'ubuntu')

  def testFormatUsername(self):
    """Tests the _FormatUsername function."""
    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    username_string = self._output_module._FormatUsername(event_data)
    self.assertEqual(username_string, '-')

  def testGetOutputValues(self):
    """Tests the _GetOutputValues function."""
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    formatters_manager.FormattersManager.RegisterFormatter(
        formatters_test_lib.TestEventFormatter)

    try:
      output_values = self._output_module._GetOutputValues(
          event, event_data, event_data_stream, None)
    finally:
      formatters_manager.FormattersManager.DeregisterFormatter(
          formatters_test_lib.TestEventFormatter)

    self.assertEqual(len(output_values), 17)

    expected_output_values = [
        '06/27/2012',
        '18:17:01',
        'UTC',
        '....',
        'FILE',
        'Test log file',
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
        'test_parser',
        'a_binary_field: binary; my_number: 123; some_additional_foo: True']

    self.assertEqual(output_values, expected_output_values)

    event.timestamp = -9223372036854775808

    formatters_manager.FormattersManager.RegisterFormatter(
        formatters_test_lib.TestEventFormatter)

    try:
      output_values = self._output_module._GetOutputValues(
          event, event_data, event_data_stream, None)
    finally:
      formatters_manager.FormattersManager.DeregisterFormatter(
          formatters_test_lib.TestEventFormatter)

    self.assertEqual(len(output_values), 17)

    expected_output_values[0] = '00/00/0000'
    expected_output_values[1] = '--:--:--'
    expected_output_values[2] = '-'
    self.assertEqual(output_values, expected_output_values)

  # TODO: add coverage for _WriteOutputValues

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    formatters_manager.FormattersManager.RegisterFormatter(
        formatters_test_lib.TestEventFormatter)

    try:
      self._output_module.WriteEventBody(
          event, event_data, event_data_stream, event_tag)
    finally:
      formatters_manager.FormattersManager.DeregisterFormatter(
          formatters_test_lib.TestEventFormatter)

    expected_event_body = (
        '06/27/2012,18:17:01,UTC,M...,FILE,Test log file,Content Modification '
        'Time,-,ubuntu,Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
        'session closed for user root),Reporter <CRON> PID: 8442 '
        '(pam_unix(cron:session): session closed for user root),'
        '2,log/syslog.1,-,Malware Printed,test_parser,a_binary_field: binary; '
        'my_number: 123; some_additional_foo: True\n')

    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, expected_event_body)

    # Ensure that the only commas returned are the 16 delimiters.
    self.assertEqual(event_body.count(','), 16)

  # TODO: add coverage for WriteEventMACBGroup

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = (
        'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        'version,filename,inode,notes,format,extra\n')

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)


if __name__ == '__main__':
  unittest.main()
