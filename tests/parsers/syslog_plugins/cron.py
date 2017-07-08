#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""

import unittest

from plaso.lib import timelib

from tests import test_lib as shared_test_lib
from tests.parsers.syslog_plugins import test_lib


class SyslogCronPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the cron syslog plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_cron.log'])
  def testParse(self):
    """Tests the parsing functionality on a sample file."""
    knowledge_base_values = {u'year': 2015}

    storage_writer = self._ParseFileWithPlugin(
        [u'syslog_cron.log'], u'cron',
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetSortedEvents())

    event = events[1]

    self.assertEqual(event.data_type, u'syslog:cron:task_run')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-03-11 19:26:39')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_command = u'sleep $(( 1 * 60 )); touch /tmp/afile.txt'
    self.assertEqual(event.command, expected_command)

    self.assertEqual(event.username, u'root')

    event = events[7]
    self.assertEqual(event.command, u'/sbin/status.mycheck')
    self.assertEqual(event.pid, 31067)


if __name__ == '__main__':
  unittest.main()
