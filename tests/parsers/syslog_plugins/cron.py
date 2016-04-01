# -*- coding: utf-8 -*-
"""Tests for the cron syslog plugin."""
import unittest

from tests.parsers.syslog_plugins import test_lib
from plaso.parsers.syslog_plugins import cron

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
    print event.__dict__
    self.assertEqual(cron.CronTaskRunEvent.DATA_TYPE, event.DATA_TYPE)


if __name__ == '__main__':
  unittest.main()
