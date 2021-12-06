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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'command': 'sleep $(( 1 * 60 )); touch /tmp/afile.txt',
        'date_time': '2015-03-11 19:26:39',
        'data_type': 'syslog:cron:task_run',
        'username': 'root'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2016-01-22 07:54:01',
        'data_type': 'syslog:cron:task_run',
        'command': '/sbin/status.mycheck',
        'pid': 31067,
        'username': 'root'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    knowledge_base_values = {'year': 2015}

    storage_writer = self._ParseFileWithPlugin(
        ['syslog_cron.log'], 'cron',
        knowledge_base_values=knowledge_base_values, timezone='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'command': 'sleep $(( 1 * 60 )); touch /tmp/afile.txt',
        'date_time': '2015-03-11 19:26:39',
        'data_type': 'syslog:cron:task_run',
        'timestamp': '2015-03-11 18:26:39.000000',
        'username': 'root'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
