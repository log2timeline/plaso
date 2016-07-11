#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

import unittest

from plaso.formatters import syslog as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import syslog

from tests.parsers import test_lib


class NewSyslogUnitTest(test_lib.ParserTestCase):
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

  def testParseRsyslog(self):
    """Tests the Parse function on an Ubuntu-style syslog file"""
    knowledge_base_values = {u'year': 2016}
    storage_writer = self._ParseFile(
        [u'syslog_rsyslog'], self._parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 8)

  def testParseOSX(self):
    """Tests the Parse function on an Ubuntu-style syslog file"""
    knowledge_base_values = {u'year': 2016}
    storage_writer = self._ParseFile(
        [u'syslog_osx'], self._parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 2)

  def testParse(self):
    """Tests the Parse function."""
    parser_object = syslog.SyslogParser()
    knowledge_base_values = {u'year': 2012}
    storage_writer = self._ParseFile(
        [u'syslog'], parser_object,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 13)

    event_object = storage_writer.events[0]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event_object.timestamp)
    self.assertEqual(event_timestamp, u'2012-01-22T07:52:33+00:00')
    self.assertEqual(event_object.hostname, u'myhostname.myhost.com')

    expected_string = (
        u'[client, pid: 30840] INFO No new content.')
    self._TestGetMessageStrings(
        event_object, expected_string, expected_string)

    event_object = storage_writer.events[6]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event_object.timestamp)
    self.assertEqual(event_timestamp, u'2012-02-29T01:15:43+00:00')

    # Testing year increment.
    event_object = storage_writer.events[8]
    event_timestamp = timelib.Timestamp.CopyToIsoFormat(
        event_object.timestamp)
    self.assertEqual(event_timestamp, u'2013-03-23T23:01:18+00:00')

    event_object = storage_writer.events[11]
    expected_msg = (
        u'[aprocess, pid: 10100] This is a multi-line message that screws up'
        u'\tmany syslog parsers.')
    expected_msg_short = (
        u'[aprocess, pid: 10100] This is a multi-line message that screws up'
        u'\tmany syslo...')
    self._TestGetMessageStrings(
        event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
