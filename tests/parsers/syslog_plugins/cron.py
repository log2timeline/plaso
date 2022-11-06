#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""

import unittest

from tests.parsers.syslog_plugins import test_lib


class CronSyslogPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the cron syslog plugin."""

  def testParse(self):
    """Tests the parsing functionality on a sample file."""
    storage_writer = self._ParseFileWithPlugin(['syslog_cron.log'], 'cron')

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': 'sleep $(( 1 * 60 )); touch /tmp/afile.txt',
        'data_type': 'syslog:cron:task_run',
        'last_written_time': '0000-03-11T19:26:39',
        'username': 'root'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
