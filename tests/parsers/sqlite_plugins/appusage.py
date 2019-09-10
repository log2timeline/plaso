#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS application usage database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import appusage as _  # pylint: disable=unused-import
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
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-05-07 18:52:02.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.application, '/Applications/Safari.app')
    self.assertEqual(event_data.app_version, '9537.75.14')
    self.assertEqual(event_data.bundle_id, 'com.apple.Safari')
    self.assertEqual(event_data.count, 1)

    expected_message = (
        '/Applications/Safari.app v.9537.75.14 '
        '(bundle: com.apple.Safari). '
        'Launched: 1 time(s)')

    expected_short_message = '/Applications/Safari.app (1 time(s))'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
