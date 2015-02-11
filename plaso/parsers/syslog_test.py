#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the syslog parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import syslog as syslog_formatter
from plaso.lib import timelib_test
from plaso.parsers import syslog
from plaso.parsers import test_lib


class SyslogUnitTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = syslog.SyslogParser()

  def testParse(self):
    """Tests the Parse function."""
    knowledge_base_values = {'year': 2012}
    test_file = self._GetTestFilePath(['syslog'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 13)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-01-22 07:52:33')
    self.assertEquals(event_objects[0].timestamp, expected_timestamp)
    self.assertEquals(event_objects[0].hostname, 'myhostname.myhost.com')

    expected_string = (
        u'[client, pid: 30840] : INFO No new content.')
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string)

    expected_msg = (
        '[aprocess, pid: 101001] : This is a multi-line message that screws up'
        'many syslog parsers.')
    expected_msg_short = (
        '[aprocess, pid: 101001] : This is a multi-line message that screws up'
        'many sys...')
    self._TestGetMessageStrings(
        event_objects[11], expected_msg, expected_msg_short)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-02-29 01:15:43')
    self.assertEquals(event_objects[6].timestamp, expected_timestamp)

    # Testing year increment.
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-03-23 23:01:18')
    self.assertEquals(event_objects[8].timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
