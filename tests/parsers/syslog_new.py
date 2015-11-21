#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the new syslog parser."""

import unittest

from plaso.formatters import syslog as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import syslog_new

from tests.parsers import test_lib


class NewSyslogUnitTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = syslog_new.NewSyslogParser()

  def testParse(self):
    """Tests the Parse function."""
    knowledge_base_values = {u'year': 2012}
    test_file = self._GetTestFilePath([u'syslog'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-01-22 07:52:33')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)
    self.assertEqual(event_objects[0].hostname, u'myhostname.myhost.com')

    expected_string = (
        u'[client, pid: 30840] : INFO No new content.')
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string)

    expected_msg = (
        u'[aprocess, pid: 101001] : This is a multi-line message that screws up'
        u'many syslog parsers.')
    expected_msg_short = (
        u'[aprocess, pid: 101001] : This is a multi-line message that screws up'
        u'many sys...')
    self._TestGetMessageStrings(
        event_objects[11], expected_msg, expected_msg_short)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-02-29 01:15:43')
    self.assertEqual(event_objects[6].timestamp, expected_timestamp)

    # Testing year increment.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-23 23:01:18')
    self.assertEqual(event_objects[8].timestamp, expected_timestamp)

    self.assertEqual(len(event_objects), 13)

if __name__ == '__main__':
  unittest.main()
