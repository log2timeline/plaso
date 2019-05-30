#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""

from __future__ import unicode_literals

import unittest

from tests import test_lib as shared_test_lib
from tests.parsers.syslog_plugins import test_lib


class CronSyslogPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the cron syslog plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['syslog_cron.log'])
  def testParse(self):
    """Tests the parsing functionality on a sample file."""
    knowledge_base_values = {'year': 2015}

    storage_writer = self._ParseFileWithPlugin(
        ['syslog_cron.log'], 'cron',
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetSortedEvents())

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2015-03-11 19:26:39.000000')

    self.assertEqual(event.data_type, 'syslog:cron:task_run')

    expected_command = 'sleep $(( 1 * 60 )); touch /tmp/afile.txt'
    self.assertEqual(event.command, expected_command)

    self.assertEqual(event.username, 'root')

    event = events[7]
    self.assertEqual(event.command, '/sbin/status.mycheck')
    self.assertEqual(event.pid, 31067)


if __name__ == '__main__':
  unittest.main()
