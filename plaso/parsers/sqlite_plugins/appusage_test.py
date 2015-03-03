#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X application usage database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import appusage as appusage_formatter
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import test_lib
from plaso.parsers.sqlite_plugins import appusage


class ApplicationUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mac OS X application usage activity database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = appusage.ApplicationUsagePlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['application_usage.sqlite'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The sqlite database contains 5 events.
    self.assertEqual(len(event_objects), 5)

    # Check the first event.
    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-05-07 18:52:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.application, u'/Applications/Safari.app')
    self.assertEqual(event_object.app_version, u'9537.75.14')
    self.assertEqual(event_object.bundle_id, u'com.apple.Safari')
    self.assertEqual(event_object.count, 1)

    expected_msg = (
        u'/Applications/Safari.app v.9537.75.14 '
        u'(bundle: com.apple.Safari). '
        u'Launched: 1 time(s)')

    expected_msg_short = u'/Applications/Safari.app (1 time(s))'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
