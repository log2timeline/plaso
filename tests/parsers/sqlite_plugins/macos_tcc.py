#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the macOS TCC plugin."""

from __future__ import unicode_literals

import unittest

from plaso.parsers.sqlite_plugins import macos_tcc

from tests.parsers.sqlite_plugins import test_lib


class MacOSTCCPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS TCC plugin."""

  def testProcess(self):
    """Tests the Process function on a macOS TCC file."""
    plugin = macos_tcc.MacOSTCCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['TCC-test.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 21)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2020-05-29 12:09:51.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = ('Service: kTCCServiceUbiquity Client: com.apple.weather'
                        ' Allowed: True Prompt count: 1')

    expected_short_message = 'kTCCServiceUbiquity: com.apple.weather'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2020-05-29 12:09:51.000000',
        'service': 'kTCCServiceUbiquity',
        'client': 'com.apple.weather',
        'allowed': 1,
        'prompt_count': 1
    }
    self.CheckEventValues(storage_writer, event, expected_event_values)


if __name__ == '__main__':
  unittest.main()
