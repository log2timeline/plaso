#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""

import unittest

from plaso.lib import timelib
from plaso.parsers.syslog_plugins import cron

from tests import test_lib as shared_test_lib
from tests.parsers.syslog_plugins import test_lib


class SyslogCronPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the cron syslog plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_cron.log'])
  def testParse(self):
    """Tests the parsing functionality on a sample file."""
    storage_writer = self._ParseFileWithPlugin(
        [u'syslog_cron.log'], u'cron')

    self.assertEqual(len(storage_writer.events), 9)

    event = storage_writer.events[1]
    self.assertEqual(cron.CronTaskRunEvent.DATA_TYPE, event.DATA_TYPE)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-11 19:26:39')
    self.assertEqual(expected_timestamp, event.timestamp)
    expected_command = u'sleep $(( 1 * 60 )); touch /tmp/afile.txt'
    self.assertEqual(expected_command, event.command)
    expected_username = u'root'
    self.assertEqual(expected_username, event.username)

    event = storage_writer.events[8]
    expected_command = u'/sbin/status.mycheck'
    self.assertEqual(expected_command, event.command)
    expected_pid = 31067
    self.assertEqual(expected_pid, event.pid)


if __name__ == '__main__':
  unittest.main()
