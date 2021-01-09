#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

import unittest

from plaso.parsers import syslog

from tests.parsers import test_lib


class SyslogParserTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  def testParseRsyslog(self):
    """Tests the Parse function on a rsyslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog'], parser, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

  def testParseRsyslogTraditional(self):
    """Tests the Parse function on a traditional rsyslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog_traditional'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'myhostname.myhost.com',
        'reporter': 'Job',
        'severity': None,
        'timestamp': '2016-01-22 07:54:32.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseDarwin(self):
    """Tests the Parse function on an Darwin-style syslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_osx'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

  def testParseChromeOS(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_chromeos'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'body': 'cleanup_logs: job completed',
        'data_type': 'syslog:line',
        'reporter': 'periodic_scheduler',
        'pid': 13707,
        'severity': 'INFO',
        'timestamp': '2016-10-25 19:37:23.297265'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'reporter': 'kernel',
        'severity': 'DEBUG',
        'timestamp': '2016-10-25 19:37:24.987014'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Testing year increment.
    expected_event_values = {
        'data_type': 'syslog:line',
        'reporter': 'kernel',
        'severity': 'DEBUG',
        'timestamp': '2016-10-25 19:37:24.993079'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'reporter': 'kernel',
        'severity': 'ERR'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'body': (
            '[  316.587330] cfg80211: This is a multi-line\n\tmessage that '
            'screws up many syslog parsers.'),
        'data_type': 'syslog:line',
        'reporter': 'aprocess',
        'severity': 'INFO'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

  def testParse(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2012}
    storage_writer = self._ParseFile(
        ['syslog'], parser, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 16)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'body': 'INFO No new content in ímynd.dd.',
        'data_type': 'syslog:line',
        'hostname': 'myhostname.myhost.com',
        'pid': 30840,
        'reporter': 'client',
        'severity': None,
        'timestamp': '2012-01-22 07:52:33.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'reporter': '---',
        'severity': None,
        'timestamp': '2012-02-29 01:15:43.000000'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    # Testing year increment.
    expected_event_values = {
        'body': 'This syslog message has a fractional value for seconds.',
        'data_type': 'syslog:line',
        'reporter': 'somrandomexe',
        'severity': None,
        'timestamp': '2013-03-23 23:01:18.000000'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'reporter': '/sbin/anacron',
        'severity': None}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'body': (
            'This is a multi-line message that screws up\n\tmany syslog '
            'parsers.'),
        'data_type': 'syslog:line',
        'pid': 10100,
        'reporter': 'aprocess',
        'severity': None}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_event_values = {
        'body': '[997.390602] sda2: rw=0, want=65, limit=2',
        'data_type': 'syslog:line',
        'hostname': None,
        'reporter': 'kernel',
        'severity': None}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    # Testing non-leap year.
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['syslog'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 2)
    self.assertEqual(storage_writer.number_of_events, 15)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog_traditional'], parser,
        knowledge_base_values=knowledge_base_values, timezone='CET')

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line',
        'hostname': 'myhostname.myhost.com',
        'reporter': 'Job',
        'severity': None,
        'timestamp': '2016-01-22 06:54:32.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
