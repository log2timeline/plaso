#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the launchd plist plugin."""

import unittest

from plaso.parsers.plist_plugins import launchd

from tests.parsers.plist_plugins import test_lib


class LaunchdPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the launchd plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'launchd.plist'

    plugin = launchd.LaunchdPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetSortedEvents())

    expected_description = (
        'Launchd service config com.foobar.test points to /Test --flag arg1 '
        'with user:nobody group:nobody')

    expected_event_values = {
        'desc': expected_description,
        'key': 'launchdServiceConfig',
        'root': '/',
        'timestamp': 0}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
