# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""
import unittest

from plaso.lib import timelib
from plaso.parsers.syslog_plugins import cron

from tests.parsers.syslog_plugins import test_lib


class SyslogCronPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = cron.CronPlugin()

  def testParse(self):
    """Tests the parsing functionality on a sample file."""
    test_file = self._GetTestFilePath([u'syslog_cron.log'])
    event_queue_consumer = self._ParseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 9)

    event = event_objects[1]
    self.assertEqual(cron.CronTaskRunEvent.DATA_TYPE, event.DATA_TYPE)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-11 19:26:39')
    self.assertEqual(expected_timestamp, event.timestamp)
    expected_command = u'sleep $(( 1 * 60 )); touch /tmp/afile.txt'
    self.assertEqual(expected_command, event.command)
    expected_username = u'root'
    self.assertEqual(expected_username, event.username)

    event = event_objects[8]
    expected_command = u'/sbin/status.mycheck'
    self.assertEqual(expected_command, event.command)
    expected_pid = 31067
    self.assertEqual(expected_pid, event.pid)


if __name__ == '__main__':
  unittest.main()
