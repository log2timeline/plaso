#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS application usage database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import appusage

from tests.parsers.sqlite_plugins import test_lib


class ApplicationUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS application usage activity database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = appusage.ApplicationUsagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['application_usage.sqlite'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # Check the first event.
    expected_event_values = {
        'application': '/Applications/Safari.app',
        'app_version': '9537.75.14',
        'bundle_id': 'com.apple.Safari',
        'count': 1,
        'data_type': 'macosx:application_usage',
        'timestamp': '2014-05-07 18:52:02.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
