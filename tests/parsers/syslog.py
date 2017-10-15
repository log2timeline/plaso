#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import syslog as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import syslog

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SyslogParserTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  @shared_test_lib.skipUnlessHasTestFile(['syslog_rsyslog'])
  def testParseRsyslog(self):
    """Tests the Parse function on an Ubuntu-style syslog file"""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_rsyslog'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 8)

  @shared_test_lib.skipUnlessHasTestFile(['syslog_osx'])
  def testParseDarwin(self):
    """Tests the Parse function on an Darwin-style syslog file"""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_osx'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 2)

  @shared_test_lib.skipUnlessHasTestFile(['syslog_chromeos'])
  def testParseChromeOS(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2016}
    storage_writer = self._ParseFile(
        ['syslog_chromeos'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    event = events[0]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, '2016-10-25T19:37:23.297265+00:00')

    expected_message = (
        'INFO [periodic_scheduler, pid: 13707] cleanup_logs: job completed')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[2]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, '2016-10-25T19:37:24.987014+00:00')

    # Testing year increment.
    event = events[4]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, '2016-10-25T19:37:24.993079+00:00')

    event = events[6]
    expected_reporter = 'kernel'
    self.assertEqual(event.reporter, expected_reporter)

    event = events[7]
    expected_message = (
        'INFO [aprocess] [  316.587330] cfg80211: This is a multi-line\t'
        'message that screws up many syslog parsers.')
    expected_short_message = (
        'INFO [aprocess] [  316.587330] cfg80211: This is a multi-line\t'
        'message that sc...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['syslog'])
  def testParse(self):
    """Tests the Parse function."""
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2012}
    storage_writer = self._ParseFile(
        ['syslog'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 16)

    events = list(storage_writer.GetEvents())

    event = events[0]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, '2012-01-22T07:52:33+00:00')
    self.assertEqual(event.hostname, 'myhostname.myhost.com')

    expected_message = (
        '[client, pid: 30840] INFO No new content in ímynd.dd.')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[6]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, '2012-02-29T01:15:43+00:00')

    # Testing year increment.
    event = events[8]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, '2013-03-23T23:01:18+00:00')

    event = events[10]
    expected_reporter = '/sbin/anacron'
    self.assertEqual(event.reporter, expected_reporter)

    event = events[11]
    expected_message = (
        '[aprocess, pid: 10100] This is a multi-line message that screws up'
        '\tmany syslog parsers.')
    expected_short_message = (
        '[aprocess, pid: 10100] This is a multi-line message that screws up'
        '\tmany syslo...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[14]
    self.assertEqual(event.reporter, 'kernel')
    self.assertIsNone(event.hostname)
    expected_message = (
        '[kernel] [997.390602] sda2: rw=0, want=65, limit=2')
    expected_short_message = (
        '[kernel] [997.390602] sda2: rw=0, want=65, limit=2')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Testing non-leap year.
    parser = syslog.SyslogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['syslog'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 15)


if __name__ == '__main__':
  unittest.main()
