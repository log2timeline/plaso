#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Car Play Application plist plugin."""

import unittest

from plaso.parsers.plist_plugins import ios_carplay

from tests.parsers.plist_plugins import test_lib


class IOSCarPlayPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the iOS Car Play Application plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.CarPlayApp.plist'

    plugin = ios_carplay.IOSCarPlayPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2020-04-12 13:55:51.255235072',
        'desc': 'com.apple.mobilecal'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
