#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome extension activity database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import chrome_extension_activity

from tests.parsers.sqlite_plugins import test_lib


class ChromeExtensionActivityPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome extension activity database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome extension activity database."""
    plugin = chrome_extension_activity.ChromeExtensionActivityPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['Extension Activity'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 56)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action_type': 1,
        'activity_id': 48,
        'api_name': 'browserAction.onClicked',
        'data_type': 'chrome:extension_activity:activity_log',
        'extension_id': 'ognampngfcbddbfemdapefohjiobgbdl',
        'timestamp': '2014-11-25 21:08:23.698737',
        'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
