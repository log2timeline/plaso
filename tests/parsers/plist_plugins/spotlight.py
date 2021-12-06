#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the spotlight plist plugin."""

import unittest

from plaso.parsers.plist_plugins import spotlight

from tests.parsers.plist_plugins import test_lib


class SpotlightPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the spotlight plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.spotlight.plist'

    plugin = spotlight.SpotlightPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1375236414408299, 1376696381196456, 1379937262090907, 1380942616952360,
        1386111811136094, 1386951868185478, 1387822901900938, 1388331212005130,
        1389056477460443]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': (
            'Spotlight term searched "gr" associate to Grab '
            '(/Applications/Utilities/Grab.app)'),
        'key': 'gr',
        'root': '/UserShortcuts'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)


if __name__ == '__main__':
  unittest.main()
