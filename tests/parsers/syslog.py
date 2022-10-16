#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

import unittest

from plaso.parsers import syslog

from tests.parsers import test_lib


class SyslogParserTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = syslog.SyslogParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins), number_of_plugins)

    parser.EnablePlugins(['cron'])
    self.assertEqual(len(parser._plugins), 1)

  def testParseRsyslog(self):
    """Tests the Parse function on a rsyslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2020}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog'], parser, knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseRsyslogTraditional(self):
    """Tests the Parse function on a traditional rsyslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog_traditional'], parser,
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2016-01-22T07:54:32',
        'hostname': 'myhostname.myhost.com',
        'reporter': 'Job',
        'severity': None}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseRsyslogProtocol23(self):
    """Tests the Parse function on a protocol 23 rsyslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2021}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog_SyslogProtocol23Format'], parser,
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2021-03-06T04:07:38.251122+00:00',
        'hostname': 'hostname',
        'reporter': 'log_tag',
        'severity': 'DEBUG'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseRsyslogSysklogd(self):
    """Tests the Parse function on a syslogkd format rsyslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2021}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog_SysklogdFileFormat'], parser,
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2021-03-06T04:07:28',
        'hostname': 'hostname',
        'reporter': 'log_tag',
        'severity': None}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseDarwin(self):
    """Tests the Parse function on an Darwin-style syslog file."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_osx'], parser,
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseChromeOS(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_chromeos'], parser,
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Note that syslog_chromeos contains -07:00 as time zone offset.
    expected_event_values = {
        'body': 'cleanup_logs: job completed',
        'data_type': 'syslog:line',
        'date_time': '2016-10-25T12:37:23.297265-07:00',
        'reporter': 'periodic_scheduler',
        'pid': 13707,
        'severity': 'INFO',
        'timestamp': '2016-10-25 19:37:23.297265'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2016-10-25T12:37:24.987014-07:00',
        'reporter': 'kernel',
        'severity': 'DEBUG'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Testing year increment.
    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2016-10-25T12:37:24.993079-07:00',
        'reporter': 'kernel',
        'severity': 'DEBUG'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2016-10-25T12:37:25.007963-07:00',
        'reporter': 'kernel',
        'severity': 'ERR'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'body': (
            '[  316.587330] cfg80211: This is a multi-line\n\tmessage that '
            'screws up many syslog parsers.'),
        'data_type': 'syslog:line',
        'date_time': '2016-10-25T12:37:25.014015-07:00',
        'reporter': 'aprocess',
        'severity': 'INFO'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

  def testParse(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2012}
    storage_writer = self._ParseFile(
        ['syslog'], parser, knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 16)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'body': 'INFO No new content in ímynd.dd.',
        'data_type': 'syslog:line',
        'date_time': '2012-01-22T07:52:33',
        'hostname': 'myhostname.myhost.com',
        'pid': 30840,
        'reporter': 'client',
        'severity': None}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2012-02-29T01:15:43',
        'reporter': '---',
        'severity': None}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    # Testing year increment.
    expected_event_values = {
        'body': 'This syslog message has a fractional value for seconds.',
        'data_type': 'syslog:line',
        'date_time': '2013-03-23T23:01:18',
        'reporter': 'somrandomexe',
        'severity': None}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2013-12-31T17:54:32',
        'reporter': '/sbin/anacron',
        'severity': None}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'body': (
            'This is a multi-line message that screws up\n\tmany syslog '
            'parsers.'),
        'data_type': 'syslog:line',
        'date_time': '2013-11-18T01:15:20',
        'pid': 10100,
        'reporter': 'aprocess',
        'severity': None}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_event_values = {
        'body': '[997.390602] sda2: rw=0, want=65, limit=2',
        'data_type': 'syslog:line',
        'date_time': '2014-11-18T08:30:20',
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 15)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog_traditional'], parser,
        knowledge_base_values=knowledge_base_values, time_zone_string='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line',
        'date_time': '2016-01-22T07:54:32',
        'hostname': 'myhostname.myhost.com',
        'reporter': 'Job',
        'severity': None,
        'timestamp': '2016-01-22 06:54:32.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
