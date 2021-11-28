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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'plist:key',
        'date_time': 'Not set',
        'desc': (
            'Launchd service config com.foobar.test points to /Test --flag '
            'arg1 with user:nobody group:nobody'),
        'key': 'launchdServiceConfig',
        'root': '/'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
