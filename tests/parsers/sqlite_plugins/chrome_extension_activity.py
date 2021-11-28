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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 56)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action_type': 1,
        'activity_id': 48,
        'api_name': 'browserAction.onClicked',
        'data_type': 'chrome:extension_activity:activity_log',
        'date_time': '2014-11-25 21:08:23.698737',
        'extension_id': 'ognampngfcbddbfemdapefohjiobgbdl',
        'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
