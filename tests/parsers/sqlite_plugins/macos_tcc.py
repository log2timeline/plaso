#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the macOS TCC plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
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

    expected_event_values = {
        'allowed': 1,
        'client': 'com.apple.weather',
        'service': 'kTCCServiceUbiquity',
        'prompt_count': 1,
        'timestamp': '2020-05-29 12:09:51.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_PROMPTED_USER}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Service: kTCCServiceUbiquity '
        'Client: com.apple.weather '
        'Allowed: True '
        'Prompt count: 1')
    expected_short_message = 'kTCCServiceUbiquity: com.apple.weather'

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
