#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

import unittest

from plaso.formatters import syslog  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import syslog

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SyslogParserTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = syslog.SyslogParser()
    # We don't want to test syslog plugins, just the parser
    self.plugins = [plugin for _, plugin in list(self._parser.GetPlugins())]
    for plugin in self.plugins:
      syslog.SyslogParser.DeregisterPlugin(plugin)

  def tearDown(self):
    """Cleans up after running an individual test."""
    syslog.SyslogParser.RegisterPlugins(self.plugins)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_rsyslog'])
  def testParseRsyslog(self):
    """Tests the Parse function on an Ubuntu-style syslog file"""
    knowledge_base_values = {u'year': 2016}
    storage_writer = self._ParseFile(
        [u'syslog_rsyslog'], self._parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 8)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_osx'])
  def testParseDarwin(self):
    """Tests the Parse function on an Darwin-style syslog file"""
    knowledge_base_values = {u'year': 2016}
    storage_writer = self._ParseFile(
        [u'syslog_osx'], self._parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 2)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = syslog.SyslogParser()
    knowledge_base_values = {u'year': 2012}
    storage_writer = self._ParseFile(
        [u'syslog'], parser_object,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 16)

    event = storage_writer.events[0]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, u'2012-01-22T07:52:33+00:00')
    self.assertEqual(event.hostname, u'myhostname.myhost.com')

    expected_string = (
        u'[client, pid: 30840] INFO No new content in ímynd.dd.')
    self._TestGetMessageStrings(
        event, expected_string, expected_string)

    event = storage_writer.events[6]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, u'2012-02-29T01:15:43+00:00')

    # Testing year increment.
    event = storage_writer.events[8]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp)
    self.assertEqual(event_timestamp, u'2013-03-23T23:01:18+00:00')

    event = storage_writer.events[10]
    expected_reporter = u'/sbin/anacron'
    self.assertEqual(event.reporter, expected_reporter)

    event = storage_writer.events[11]
    expected_message = (
        u'[aprocess, pid: 10100] This is a multi-line message that screws up'
        u'\tmany syslog parsers.')
    expected_message_short = (
        u'[aprocess, pid: 10100] This is a multi-line message that screws up'
        u'\tmany syslo...')
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[14]
    self.assertEqual(event.reporter, u'kernel')
    self.assertIsNone(event.hostname)
    expected_message = (
        u'[kernel] [997.390602] sda2: rw=0, want=65, limit=2')
    expected_message_short = (
        u'[kernel] [997.390602] sda2: rw=0, want=65, limit=2')
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
