#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""

import unittest

from tests.parsers.syslog_plugins import test_lib


class CronSyslogPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the cron syslog plugin."""

  def testParse(self):
    """Tests the parsing functionality on a sample file."""
    knowledge_base_values = {'year': 2015}

    storage_writer = self._ParseFileWithPlugin(
        ['syslog_cron.log'], 'cron',
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'command': 'sleep $(( 1 * 60 )); touch /tmp/afile.txt',
        'data_type': 'syslog:cron:task_run',
        'timestamp': '2015-03-11 19:26:39.000000',
        'username': 'root'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'syslog:cron:task_run',
        'command': '/sbin/status.mycheck',
        'pid': 31067,
        'timestamp': '2016-01-22 07:54:01.000000',
        'username': 'root'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)


if __name__ == '__main__':
  unittest.main()
