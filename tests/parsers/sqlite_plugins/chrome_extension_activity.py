#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome extension activity database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_extension_activity as _  # pylint: disable=unused-import
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

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-11-25 21:08:23.698737')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UNKNOWN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_extension_id = 'ognampngfcbddbfemdapefohjiobgbdl'
    self.assertEqual(event_data.extension_id, expected_extension_id)

    self.assertEqual(event_data.action_type, 1)
    self.assertEqual(event_data.activity_id, 48)
    self.assertEqual(event_data.api_name, 'browserAction.onClicked')

    expected_message = (
        'Chrome extension: ognampngfcbddbfemdapefohjiobgbdl '
        'Action type: API event callback (type 1) '
        'Activity identifier: 48 '
        'API name: browserAction.onClicked')
    expected_short_message = (
        'ognampngfcbddbfemdapefohjiobgbdl browserAction.onClicked')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
