#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import syslog as _  # pylint: disable=unused-import
from plaso.parsers import syslog

from tests.parsers import test_lib


class SyslogParserTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  def testParseRsyslog(self):
    """Tests the Parse function on an Ubuntu-style syslog file"""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

  def testParseDarwin(self):
    """Tests the Parse function on an Darwin-style syslog file"""
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

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2016-10-25 19:37:23.297265')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, 'periodic_scheduler')
    self.assertEqual(event_data.severity, 'INFO')

    expected_message = (
        'INFO [periodic_scheduler, pid: 13707] cleanup_logs: job completed')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2016-10-25 19:37:24.987014')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, 'kernel')
    self.assertEqual(event_data.severity, 'DEBUG')

    # Testing year increment.
    event = events[4]

    self.CheckTimestamp(event.timestamp, '2016-10-25 19:37:24.993079')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, 'kernel')
    self.assertEqual(event_data.severity, 'DEBUG')

    event = events[6]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, 'kernel')
    self.assertEqual(event_data.severity, 'ERR')

    event = events[7]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, 'aprocess')
    self.assertEqual(event_data.severity, 'INFO')

    expected_message = (
        'INFO [aprocess] [  316.587330] cfg80211: This is a multi-line\t'
        'message that screws up many syslog parsers.')
    expected_short_message = (
        'INFO [aprocess] [  316.587330] cfg80211: This is a multi-line\t'
        'message that sc...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParse(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2012}
    storage_writer = self._ParseFile(
        ['syslog'], parser, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 16)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-01-22 07:52:33.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'syslog:line')
    self.assertEqual(event_data.hostname, 'myhostname.myhost.com')
    self.assertEqual(event_data.reporter, 'client')
    self.assertIsNone(event_data.severity)

    expected_message = (
        '[client, pid: 30840] INFO No new content in ímynd.dd.')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[6]

    self.CheckTimestamp(event.timestamp, '2012-02-29 01:15:43.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, '---')
    self.assertIsNone(event_data.severity)

    # Testing year increment.
    event = events[9]

    self.CheckTimestamp(event.timestamp, '2013-03-23 23:01:18.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.body,
        'This syslog message has a fractional value for seconds.')
    self.assertEqual(event_data.reporter, 'somrandomexe')
    self.assertIsNone(event_data.severity)

    event = events[11]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, '/sbin/anacron')
    self.assertIsNone(event_data.severity)

    event = events[10]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.reporter, 'aprocess')
    self.assertIsNone(event_data.severity)

    expected_message = (
        '[aprocess, pid: 10100] This is a multi-line message that screws up'
        '\tmany syslog parsers.')
    expected_short_message = (
        '[aprocess, pid: 10100] This is a multi-line message that screws up'
        '\tmany syslo...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[14]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertIsNone(event_data.hostname)
    self.assertEqual(event_data.reporter, 'kernel')
    self.assertIsNone(event_data.severity)

    expected_message = (
        '[kernel] [997.390602] sda2: rw=0, want=65, limit=2')
    expected_short_message = (
        '[kernel] [997.390602] sda2: rw=0, want=65, limit=2')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Testing non-leap year.
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['syslog'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 2)
    self.assertEqual(storage_writer.number_of_events, 15)


if __name__ == '__main__':
  unittest.main()
